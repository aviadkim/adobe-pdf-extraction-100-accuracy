#!/usr/bin/env python3
"""
Optimized Spatial Analysis for Adobe PDF Extraction System
High-performance spatial analysis and table reconstruction with caching and parallelization
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import pickle
import hashlib
from functools import lru_cache
import multiprocessing
import time
from collections import defaultdict
from scipy.spatial import KDTree
from sklearn.cluster import DBSCAN
import json

# Import our custom modules
try:
    from performance_monitor import monitor_performance, PerformanceMonitor
    from exceptions import SpatialAnalysisError, ProcessingError
except ImportError:
    def monitor_performance(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)


@dataclass
class TextElement:
    """Optimized text element representation"""
    text: str
    page: int
    x: float
    y: float
    width: float
    height: float
    font_size: float = 0.0
    font_name: str = ""
    
    @property
    def center_x(self) -> float:
        return self.x + self.width / 2
    
    @property
    def center_y(self) -> float:
        return self.y + self.height / 2
    
    @property
    def right(self) -> float:
        return self.x + self.width
    
    @property
    def bottom(self) -> float:
        return self.y + self.height
    
    def overlaps_horizontally(self, other: 'TextElement', tolerance: float = 5.0) -> bool:
        """Check if elements overlap horizontally within tolerance"""
        return not (self.right < other.x - tolerance or other.right < self.x - tolerance)
    
    def overlaps_vertically(self, other: 'TextElement', tolerance: float = 5.0) -> bool:
        """Check if elements overlap vertically within tolerance"""
        return not (self.bottom < other.y - tolerance or other.bottom < self.y - tolerance)
    
    def distance_to(self, other: 'TextElement') -> float:
        """Calculate distance between element centers"""
        dx = self.center_x - other.center_x
        dy = self.center_y - other.center_y
        return np.sqrt(dx * dx + dy * dy)


@dataclass
class TableCandidate:
    """Represents a potential table structure"""
    elements: List[TextElement]
    rows: int
    columns: int
    confidence: float
    page: int
    bounding_box: Tuple[float, float, float, float]  # x, y, width, height
    row_groups: List[List[TextElement]]
    column_alignment: List[float]  # X coordinates of column centers
    
    def get_cell_value(self, row: int, col: int) -> Optional[str]:
        """Get cell value at specific row/column"""
        if 0 <= row < len(self.row_groups):
            if 0 <= col < len(self.row_groups[row]):
                return self.row_groups[row][col].text
        return None
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert table to pandas DataFrame"""
        data = []
        max_cols = max(len(row) for row in self.row_groups) if self.row_groups else 0
        
        for row_elements in self.row_groups:
            row_data = []
            for col in range(max_cols):
                if col < len(row_elements):
                    row_data.append(row_elements[col].text)
                else:
                    row_data.append("")
            data.append(row_data)
        
        return pd.DataFrame(data)


class SpatialIndexer:
    """Efficient spatial indexing for text elements"""
    
    def __init__(self, elements: List[TextElement]):
        self.elements = elements
        self.page_indices = {}
        self._build_indices()
    
    def _build_indices(self):
        """Build spatial indices for each page"""
        pages = set(elem.page for elem in self.elements)
        
        for page in pages:
            page_elements = [elem for elem in self.elements if elem.page == page]
            
            if page_elements:
                # Create KDTree for fast spatial queries
                points = np.array([[elem.center_x, elem.center_y] for elem in page_elements])
                kdtree = KDTree(points)
                
                # Create sorted indices for range queries
                x_sorted = sorted(enumerate(page_elements), key=lambda x: x[1].x)
                y_sorted = sorted(enumerate(page_elements), key=lambda x: x[1].y)
                
                self.page_indices[page] = {
                    'elements': page_elements,
                    'kdtree': kdtree,
                    'x_sorted': x_sorted,
                    'y_sorted': y_sorted,
                    'points': points
                }
    
    def find_elements_in_region(self, page: int, x: float, y: float, 
                               width: float, height: float) -> List[TextElement]:
        """Find all elements within a rectangular region"""
        if page not in self.page_indices:
            return []
        
        index_data = self.page_indices[page]
        elements = index_data['elements']
        
        # Use spatial filtering
        result = []
        for elem in elements:
            if (elem.x < x + width and elem.right > x and
                elem.y < y + height and elem.bottom > y):
                result.append(elem)
        
        return result
    
    def find_nearest_elements(self, page: int, x: float, y: float, 
                            k: int = 5, max_distance: float = 100.0) -> List[TextElement]:
        """Find k nearest elements to a point"""
        if page not in self.page_indices:
            return []
        
        index_data = self.page_indices[page]
        kdtree = index_data['kdtree']
        elements = index_data['elements']
        
        distances, indices = kdtree.query([x, y], k=min(k, len(elements)))
        
        # Filter by max distance
        result = []
        if k == 1:
            distances, indices = [distances], [indices]
        
        for dist, idx in zip(distances, indices):
            if dist <= max_distance:
                result.append(elements[idx])
        
        return result
    
    def find_elements_in_horizontal_band(self, page: int, y: float, 
                                       tolerance: float = 10.0) -> List[TextElement]:
        """Find all elements in a horizontal band (for row detection)"""
        if page not in self.page_indices:
            return []
        
        elements = self.page_indices[page]['elements']
        return [elem for elem in elements 
                if abs(elem.center_y - y) <= tolerance]
    
    def find_elements_in_vertical_band(self, page: int, x: float, 
                                     tolerance: float = 10.0) -> List[TextElement]:
        """Find all elements in a vertical band (for column detection)"""
        if page not in self.page_indices:
            return []
        
        elements = self.page_indices[page]['elements']
        return [elem for elem in elements 
                if abs(elem.center_x - x) <= tolerance]


class OptimizedSpatialAnalyzer:
    """High-performance spatial analysis engine"""
    
    def __init__(self, enable_parallel: bool = True, cache_size: int = 128):
        self.enable_parallel = enable_parallel
        self.cache_size = cache_size
        self.performance_monitor = PerformanceMonitor()
        
        # Algorithm parameters
        self.row_tolerance = 8.0
        self.column_tolerance = 15.0
        self.min_table_rows = 2
        self.min_table_columns = 2
        self.max_table_gap_ratio = 3.0  # Max gap between elements as ratio of font size
        
    @monitor_performance(cache_ttl=3600, enable_cache=True)
    def analyze_document(self, elements_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Main entry point for document spatial analysis
        
        Args:
            elements_data: List of text element dictionaries from Adobe API
            
        Returns:
            Analysis results with tables, confidence scores, and metadata
        """
        start_time = time.time()
        
        # Convert to optimized format
        elements = self._convert_elements(elements_data)
        
        if not elements:
            return {
                'tables': [],
                'analysis_time': time.time() - start_time,
                'elements_processed': 0,
                'pages_analyzed': 0
            }
        
        # Build spatial index
        indexer = SpatialIndexer(elements)
        
        # Analyze each page
        pages = set(elem.page for elem in elements)
        all_tables = []
        
        if self.enable_parallel and len(pages) > 1:
            # Parallel page processing
            with ThreadPoolExecutor(max_workers=min(len(pages), multiprocessing.cpu_count())) as executor:
                futures = [
                    executor.submit(self._analyze_page, page, indexer)
                    for page in pages
                ]
                
                for future in futures:
                    try:
                        page_tables = future.result()
                        all_tables.extend(page_tables)
                    except Exception as e:
                        logger.error(f"Error analyzing page: {e}")
        else:
            # Sequential processing
            for page in pages:
                try:
                    page_tables = self._analyze_page(page, indexer)
                    all_tables.extend(page_tables)
                except Exception as e:
                    logger.error(f"Error analyzing page {page}: {e}")
        
        # Post-process tables
        all_tables = self._post_process_tables(all_tables)
        
        analysis_time = time.time() - start_time
        
        return {
            'tables': [self._table_to_dict(table) for table in all_tables],
            'analysis_time': analysis_time,
            'elements_processed': len(elements),
            'pages_analyzed': len(pages),
            'spatial_index_pages': len(indexer.page_indices),
            'performance_score': self._calculate_performance_score(analysis_time, len(elements))
        }
    
    def _convert_elements(self, elements_data: List[Dict[str, Any]]) -> List[TextElement]:
        """Convert Adobe API elements to optimized TextElement objects"""
        elements = []
        
        for elem_data in elements_data:
            if not elem_data.get('Text'):
                continue
            
            bounds = elem_data.get('Bounds', [0, 0, 0, 0])
            if len(bounds) < 4:
                continue
            
            font_info = elem_data.get('Font', {})
            
            try:
                element = TextElement(
                    text=elem_data['Text'].strip(),
                    page=elem_data.get('Page', 1),
                    x=float(bounds[0]),
                    y=float(bounds[1]),
                    width=float(bounds[2]),
                    height=float(bounds[3]),
                    font_size=float(font_info.get('size', 0)),
                    font_name=font_info.get('name', '')
                )
                
                # Filter out very small or empty elements
                if element.width > 1 and element.height > 1 and element.text:
                    elements.append(element)
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid element: {e}")
                continue
        
        return elements
    
    @lru_cache(maxsize=32)
    def _analyze_page(self, page: int, indexer: SpatialIndexer) -> List[TableCandidate]:
        """Analyze a single page for table structures"""
        if page not in indexer.page_indices:
            return []
        
        elements = indexer.page_indices[page]['elements']
        
        if len(elements) < self.min_table_rows * self.min_table_columns:
            return []
        
        # Step 1: Detect row groups using clustering
        row_groups = self._detect_row_groups(elements, indexer, page)
        
        if len(row_groups) < self.min_table_rows:
            return []
        
        # Step 2: Detect column alignment
        tables = []
        for row_group_set in self._group_consecutive_rows(row_groups):
            if len(row_group_set) >= self.min_table_rows:
                table = self._construct_table_from_rows(row_group_set, page)
                if table and table.confidence > 0.3:  # Minimum confidence threshold
                    tables.append(table)
        
        return tables
    
    def _detect_row_groups(self, elements: List[TextElement], 
                          indexer: SpatialIndexer, page: int) -> List[List[TextElement]]:
        """Detect horizontal row groups using DBSCAN clustering"""
        if not elements:
            return []
        
        # Prepare data for clustering
        y_positions = np.array([[elem.center_y] for elem in elements])
        
        # Use DBSCAN to find row clusters
        clustering = DBSCAN(eps=self.row_tolerance, min_samples=1).fit(y_positions)
        labels = clustering.labels_
        
        # Group elements by cluster
        clusters = defaultdict(list)
        for elem, label in zip(elements, labels):
            clusters[label].append(elem)
        
        # Convert to sorted row groups
        row_groups = []
        for cluster_elements in clusters.values():
            if len(cluster_elements) >= self.min_table_columns:
                # Sort elements in row by x position
                cluster_elements.sort(key=lambda e: e.x)
                row_groups.append(cluster_elements)
        
        # Sort row groups by y position (top to bottom)
        row_groups.sort(key=lambda row: row[0].y)
        
        return row_groups
    
    def _group_consecutive_rows(self, row_groups: List[List[TextElement]]) -> List[List[List[TextElement]]]:
        """Group consecutive rows into potential tables"""
        if not row_groups:
            return []
        
        table_groups = []
        current_group = [row_groups[0]]
        
        for i in range(1, len(row_groups)):
            prev_row = row_groups[i-1]
            curr_row = row_groups[i]
            
            # Calculate gap between rows
            prev_y = max(elem.bottom for elem in prev_row)
            curr_y = min(elem.y for elem in curr_row)
            gap = curr_y - prev_y
            
            # Estimate expected row height
            avg_height = np.mean([elem.height for elem in prev_row + curr_row])
            max_gap = avg_height * self.max_table_gap_ratio
            
            if gap <= max_gap:
                current_group.append(curr_row)
            else:
                # Gap too large, start new table group
                if len(current_group) >= self.min_table_rows:
                    table_groups.append(current_group)
                current_group = [curr_row]
        
        # Add final group
        if len(current_group) >= self.min_table_rows:
            table_groups.append(current_group)
        
        return table_groups
    
    def _construct_table_from_rows(self, row_groups: List[List[TextElement]], 
                                  page: int) -> Optional[TableCandidate]:
        """Construct table candidate from row groups"""
        if not row_groups:
            return None
        
        # Detect column alignment
        column_positions = self._detect_column_alignment(row_groups)
        
        if len(column_positions) < self.min_table_columns:
            return None
        
        # Align elements to columns
        aligned_rows = []
        for row_elements in row_groups:
            aligned_row = self._align_elements_to_columns(row_elements, column_positions)
            aligned_rows.append(aligned_row)
        
        # Calculate table boundaries
        all_elements = [elem for row in row_groups for elem in row]
        min_x = min(elem.x for elem in all_elements)
        max_x = max(elem.right for elem in all_elements)
        min_y = min(elem.y for elem in all_elements)
        max_y = max(elem.bottom for elem in all_elements)
        
        # Calculate confidence score
        confidence = self._calculate_table_confidence(aligned_rows, column_positions)
        
        return TableCandidate(
            elements=all_elements,
            rows=len(aligned_rows),
            columns=len(column_positions),
            confidence=confidence,
            page=page,
            bounding_box=(min_x, min_y, max_x - min_x, max_y - min_y),
            row_groups=aligned_rows,
            column_alignment=column_positions
        )
    
    def _detect_column_alignment(self, row_groups: List[List[TextElement]]) -> List[float]:
        """Detect column positions by analyzing element alignment across rows"""
        all_x_positions = []
        
        # Collect all x positions
        for row_elements in row_groups:
            for elem in row_elements:
                all_x_positions.append(elem.center_x)
        
        if not all_x_positions:
            return []
        
        # Use clustering to find column positions
        x_array = np.array(all_x_positions).reshape(-1, 1)
        clustering = DBSCAN(eps=self.column_tolerance, min_samples=1).fit(x_array)
        labels = clustering.labels_
        
        # Calculate column centers
        column_centers = []
        for label in set(labels):
            if label != -1:  # Ignore noise
                cluster_positions = [pos for pos, lbl in zip(all_x_positions, labels) if lbl == label]
                column_centers.append(np.mean(cluster_positions))
        
        return sorted(column_centers)
    
    def _align_elements_to_columns(self, row_elements: List[TextElement], 
                                  column_positions: List[float]) -> List[TextElement]:
        """Align row elements to detected columns"""
        aligned_elements = [None] * len(column_positions)
        
        for elem in row_elements:
            # Find closest column
            distances = [abs(elem.center_x - col_pos) for col_pos in column_positions]
            closest_col = distances.index(min(distances))
            
            # Only assign if within tolerance and slot is empty
            if distances[closest_col] <= self.column_tolerance:
                if aligned_elements[closest_col] is None:
                    aligned_elements[closest_col] = elem
                else:
                    # Choose element closest to column center
                    existing_dist = abs(aligned_elements[closest_col].center_x - column_positions[closest_col])
                    if distances[closest_col] < existing_dist:
                        aligned_elements[closest_col] = elem
        
        # Fill gaps with empty elements
        result = []
        for i, elem in enumerate(aligned_elements):
            if elem is not None:
                result.append(elem)
            else:
                # Create placeholder for empty cell
                placeholder = TextElement(
                    text="",
                    page=row_elements[0].page if row_elements else 1,
                    x=column_positions[i] - 5,
                    y=row_elements[0].y if row_elements else 0,
                    width=10,
                    height=row_elements[0].height if row_elements else 10
                )
                result.append(placeholder)
        
        return result
    
    def _calculate_table_confidence(self, aligned_rows: List[List[TextElement]], 
                                   column_positions: List[float]) -> float:
        """Calculate confidence score for table detection"""
        if not aligned_rows or not column_positions:
            return 0.0
        
        confidence_factors = []
        
        # Factor 1: Column consistency (how well aligned are columns)
        column_consistency = 0.0
        for col_idx in range(len(column_positions)):
            col_elements = [row[col_idx] for row in aligned_rows if col_idx < len(row)]
            non_empty_elements = [elem for elem in col_elements if elem.text.strip()]
            
            if len(non_empty_elements) > 1:
                positions = [elem.center_x for elem in non_empty_elements]
                std_dev = np.std(positions)
                consistency = max(0, 1 - (std_dev / self.column_tolerance))
                column_consistency += consistency
        
        if len(column_positions) > 0:
            column_consistency /= len(column_positions)
        confidence_factors.append(column_consistency)
        
        # Factor 2: Row completeness (how many cells are filled)
        total_cells = len(aligned_rows) * len(column_positions)
        filled_cells = sum(
            1 for row in aligned_rows 
            for elem in row if elem.text.strip()
        )
        completeness = filled_cells / total_cells if total_cells > 0 else 0
        confidence_factors.append(completeness)
        
        # Factor 3: Regular spacing (consistent row heights)
        if len(aligned_rows) > 1:
            row_heights = []
            for row in aligned_rows:
                non_empty = [elem for elem in row if elem.text.strip()]
                if non_empty:
                    row_heights.append(np.mean([elem.height for elem in non_empty]))
            
            if len(row_heights) > 1:
                height_std = np.std(row_heights)
                avg_height = np.mean(row_heights)
                spacing_consistency = max(0, 1 - (height_std / avg_height)) if avg_height > 0 else 0
                confidence_factors.append(spacing_consistency)
        
        # Factor 4: Content patterns (numbers, structured text)
        content_score = self._analyze_content_patterns(aligned_rows)
        confidence_factors.append(content_score)
        
        # Combine factors with weights
        weights = [0.3, 0.3, 0.2, 0.2]
        final_confidence = sum(factor * weight for factor, weight in zip(confidence_factors, weights))
        
        return min(1.0, max(0.0, final_confidence))
    
    def _analyze_content_patterns(self, aligned_rows: List[List[TextElement]]) -> float:
        """Analyze content patterns to boost table confidence"""
        if not aligned_rows:
            return 0.0
        
        pattern_scores = []
        
        # Check for numeric columns
        for col_idx in range(len(aligned_rows[0]) if aligned_rows else 0):
            col_texts = [
                row[col_idx].text.strip() for row in aligned_rows 
                if col_idx < len(row) and row[col_idx].text.strip()
            ]
            
            if len(col_texts) > 1:
                numeric_count = sum(
                    1 for text in col_texts 
                    if self._is_numeric_value(text)
                )
                numeric_ratio = numeric_count / len(col_texts)
                pattern_scores.append(numeric_ratio)
        
        # Check for header patterns (different formatting in first row)
        if len(aligned_rows) > 1:
            first_row_fonts = [elem.font_size for elem in aligned_rows[0] if elem.text.strip()]
            other_rows_fonts = [
                elem.font_size for row in aligned_rows[1:] 
                for elem in row if elem.text.strip()
            ]
            
            if first_row_fonts and other_rows_fonts:
                first_row_avg = np.mean(first_row_fonts)
                other_rows_avg = np.mean(other_rows_fonts)
                
                # Header typically has larger font
                if first_row_avg > other_rows_avg:
                    pattern_scores.append(0.8)
        
        return np.mean(pattern_scores) if pattern_scores else 0.0
    
    def _is_numeric_value(self, text: str) -> bool:
        """Check if text represents a numeric value"""
        # Remove common formatting
        clean_text = text.replace(',', '').replace('$', '').replace('%', '').strip()
        
        try:
            float(clean_text)
            return True
        except ValueError:
            return False
    
    def _post_process_tables(self, tables: List[TableCandidate]) -> List[TableCandidate]:
        """Post-process detected tables to remove overlaps and improve quality"""
        if not tables:
            return tables
        
        # Sort by confidence (highest first)
        tables.sort(key=lambda t: t.confidence, reverse=True)
        
        # Remove overlapping tables (keep higher confidence one)
        filtered_tables = []
        for table in tables:
            is_overlapping = False
            
            for existing_table in filtered_tables:
                if self._tables_overlap(table, existing_table):
                    is_overlapping = True
                    break
            
            if not is_overlapping:
                filtered_tables.append(table)
        
        return filtered_tables
    
    def _tables_overlap(self, table1: TableCandidate, table2: TableCandidate, 
                       threshold: float = 0.3) -> bool:
        """Check if two tables overlap significantly"""
        if table1.page != table2.page:
            return False
        
        # Calculate intersection area
        x1, y1, w1, h1 = table1.bounding_box
        x2, y2, w2, h2 = table2.bounding_box
        
        # Calculate intersection rectangle
        left = max(x1, x2)
        right = min(x1 + w1, x2 + w2)
        top = max(y1, y2)
        bottom = min(y1 + h1, y2 + h2)
        
        if left < right and top < bottom:
            intersection_area = (right - left) * (bottom - top)
            table1_area = w1 * h1
            table2_area = w2 * h2
            
            # Check if intersection is significant relative to either table
            overlap_ratio1 = intersection_area / table1_area if table1_area > 0 else 0
            overlap_ratio2 = intersection_area / table2_area if table2_area > 0 else 0
            
            return max(overlap_ratio1, overlap_ratio2) > threshold
        
        return False
    
    def _table_to_dict(self, table: TableCandidate) -> Dict[str, Any]:
        """Convert table candidate to dictionary format"""
        return {
            'page': table.page,
            'rows': table.rows,
            'columns': table.columns,
            'confidence': table.confidence,
            'bounding_box': table.bounding_box,
            'data': [
                [elem.text for elem in row]
                for row in table.row_groups
            ],
            'column_alignment': table.column_alignment
        }
    
    def _calculate_performance_score(self, analysis_time: float, element_count: int) -> float:
        """Calculate performance score for the analysis"""
        # Elements per second
        eps = element_count / analysis_time if analysis_time > 0 else 0
        
        # Normalize to 0-1 scale (assuming 1000 elements/second is excellent)
        performance_score = min(1.0, eps / 1000.0)
        
        return performance_score


# Factory function for easy usage
def create_spatial_analyzer(enable_parallel: bool = None, 
                          cache_size: int = 128) -> OptimizedSpatialAnalyzer:
    """
    Create optimized spatial analyzer with automatic parallel detection
    
    Args:
        enable_parallel: Enable parallel processing (auto-detect if None)
        cache_size: LRU cache size for analysis results
        
    Returns:
        Configured spatial analyzer
    """
    if enable_parallel is None:
        enable_parallel = multiprocessing.cpu_count() > 1
    
    return OptimizedSpatialAnalyzer(
        enable_parallel=enable_parallel,
        cache_size=cache_size
    )


# Convenience function for direct usage
@monitor_performance(cache_ttl=3600)
def analyze_spatial_structure(elements_data: List[Dict[str, Any]], 
                            **kwargs) -> Dict[str, Any]:
    """
    Convenience function for spatial analysis
    
    Args:
        elements_data: Text elements from Adobe PDF extraction
        **kwargs: Additional arguments for analyzer configuration
        
    Returns:
        Spatial analysis results
    """
    analyzer = create_spatial_analyzer(**kwargs)
    return analyzer.analyze_document(elements_data)


if __name__ == "__main__":
    # Test with sample data
    sample_elements = [
        {
            "Text": "Security Name",
            "Page": 1,
            "Bounds": [50, 100, 150, 20],
            "Font": {"size": 12, "name": "Arial-Bold"}
        },
        {
            "Text": "ISIN",
            "Page": 1,
            "Bounds": [220, 100, 100, 20],
            "Font": {"size": 12, "name": "Arial-Bold"}
        },
        {
            "Text": "Amount",
            "Page": 1,
            "Bounds": [340, 100, 80, 20],
            "Font": {"size": 12, "name": "Arial-Bold"}
        },
        {
            "Text": "Swiss Government Bond",
            "Page": 1,
            "Bounds": [50, 130, 150, 15],
            "Font": {"size": 10, "name": "Arial"}
        },
        {
            "Text": "CH0123456789",
            "Page": 1,
            "Bounds": [220, 130, 100, 15],
            "Font": {"size": 10, "name": "Arial"}
        },
        {
            "Text": "100,000",
            "Page": 1,
            "Bounds": [340, 130, 80, 15],
            "Font": {"size": 10, "name": "Arial"}
        }
    ]
    
    print("Testing optimized spatial analysis...")
    
    start_time = time.time()
    result = analyze_spatial_structure(sample_elements, enable_parallel=False)
    analysis_time = time.time() - start_time
    
    print(f"\nAnalysis completed in {analysis_time:.3f}s")
    print(f"Tables found: {len(result['tables'])}")
    print(f"Elements processed: {result['elements_processed']}")
    print(f"Performance score: {result.get('performance_score', 0):.3f}")
    
    if result['tables']:
        table = result['tables'][0]
        print(f"\nFirst table:")
        print(f"  Rows: {table['rows']}, Columns: {table['columns']}")
        print(f"  Confidence: {table['confidence']:.3f}")
        print(f"  Data preview: {table['data'][:2]}")  # First 2 rows