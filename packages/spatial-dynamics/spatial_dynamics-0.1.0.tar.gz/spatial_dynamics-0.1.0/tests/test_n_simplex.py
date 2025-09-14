"""Tests for n-simplex neighborhood analysis functionality."""

import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from spatial_dynamics import n_wise_logOdds


class TestNSimplexAnalysis:
    """Test class for n-simplex neighborhood analysis."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample spatial data with three cell types for testing."""
        np.random.seed(42)
        n_cells_per_type = 50
        
        # Create three clusters of cells
        cluster1_x = np.random.normal(20, 5, n_cells_per_type)
        cluster1_y = np.random.normal(20, 5, n_cells_per_type)
        cluster1_type = ['TypeA'] * n_cells_per_type
        
        cluster2_x = np.random.normal(80, 5, n_cells_per_type)
        cluster2_y = np.random.normal(20, 5, n_cells_per_type)
        cluster2_type = ['TypeB'] * n_cells_per_type
        
        cluster3_x = np.random.normal(50, 5, n_cells_per_type)
        cluster3_y = np.random.normal(80, 5, n_cells_per_type)
        cluster3_type = ['TypeC'] * n_cells_per_type
        
        data = pd.DataFrame({
            'x': np.concatenate([cluster1_x, cluster2_x, cluster3_x]),
            'y': np.concatenate([cluster1_y, cluster2_y, cluster3_y]),
            'cluster': cluster1_type + cluster2_type + cluster3_type
        })
        
        return data
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory for test outputs."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
    
    def test_basic_nsimplex_analysis(self, sample_data, temp_output_dir):
        """Test basic n-simplex analysis."""
        target_types = ['TypeA', 'TypeB', 'TypeC']
        
        neighbor_matrix, global_log_odds = n_wise_logOdds(
            spatial_obj=sample_data,
            out_dir=temp_output_dir,
            label='test_nsimplex',
            target_celltypes=target_types,
            compute_effect_size=False
        )
        
        # Check return types and structure
        assert isinstance(neighbor_matrix, pd.DataFrame)
        assert isinstance(global_log_odds, (float, np.float64))
        assert neighbor_matrix.shape == (3, 3)  # 3 cell types
        assert all(col in target_types for col in neighbor_matrix.columns)
        assert all(idx in ['TypeA', 'TypeB', 'TypeC'] for idx in neighbor_matrix.index)
        
        # Check output files exist
        assert os.path.exists(os.path.join(temp_output_dir, 'test_nsimplex-logOdds_matrix.csv'))
        assert os.path.exists(os.path.join(temp_output_dir, 'test_nsimplex-probabilities_matrix.csv'))
    
    def test_nsimplex_with_effect_sizes(self, sample_data, temp_output_dir):
        """Test n-simplex analysis with effect size computation."""
        target_types = ['TypeA', 'TypeB']
        
        neighbor_matrix, global_log_odds = n_wise_logOdds(
            spatial_obj=sample_data,
            out_dir=temp_output_dir,
            label='test_nsimplex_effects',
            target_celltypes=target_types,
            compute_effect_size=True
        )
        
        # Check basic structure
        assert isinstance(neighbor_matrix, pd.DataFrame)
        assert isinstance(global_log_odds, (float, np.float64))
        assert neighbor_matrix.shape == (3, 2)  # All cell types vs target types
        
        # Check effect sizes file exists
        assert os.path.exists(os.path.join(temp_output_dir, 'test_nsimplex_effects-KS-effect_sizes_matrix.csv'))
    
    def test_nsimplex_default_target_types(self, sample_data, temp_output_dir):
        """Test n-simplex analysis with default target cell types (all types)."""
        neighbor_matrix, global_log_odds = n_wise_logOdds(
            spatial_obj=sample_data,
            out_dir=temp_output_dir,
            label='test_default_targets',
            target_celltypes=None,  # Should use all cell types
            compute_effect_size=False
        )
        
        assert isinstance(neighbor_matrix, pd.DataFrame)
        assert isinstance(global_log_odds, (float, np.float64))
        # All 3 cell types should be used as both targets and references
        assert neighbor_matrix.shape == (3, 3)
    
    def test_nsimplex_subset_target_types(self, sample_data, temp_output_dir):
        """Test n-simplex analysis with subset of target cell types."""
        target_types = ['TypeA', 'TypeB']  # Only 2 of 3 types
        
        neighbor_matrix, global_log_odds = n_wise_logOdds(
            spatial_obj=sample_data,
            out_dir=temp_output_dir,
            label='test_subset_targets',
            target_celltypes=target_types,
            compute_effect_size=False
        )
        
        assert isinstance(neighbor_matrix, pd.DataFrame)
        assert isinstance(global_log_odds, (float, np.float64))
        # 3 reference types (rows) vs 2 target types (columns)
        assert neighbor_matrix.shape == (3, 2)
        assert list(neighbor_matrix.columns) == target_types
    
    def test_nsimplex_custom_parameters(self, sample_data, temp_output_dir):
        """Test n-simplex analysis with custom parameters."""
        neighbor_matrix, global_log_odds = n_wise_logOdds(
            spatial_obj=sample_data,
            out_dir=temp_output_dir,
            label='test_custom_params',
            target_celltypes=['TypeA', 'TypeB'],
            resolution=0.5,
            p1=5,
            p2=25,
            compute_effect_size=False
        )
        
        assert isinstance(neighbor_matrix, pd.DataFrame)
        assert isinstance(global_log_odds, (float, np.float64))
        assert neighbor_matrix.shape == (3, 2)
    
    def test_nsimplex_invalid_target_types(self, sample_data, temp_output_dir):
        """Test handling of invalid target cell types."""
        with pytest.raises(KeyError):
            n_wise_logOdds(
                spatial_obj=sample_data,
                out_dir=temp_output_dir,
                label='test_invalid_targets',
                target_celltypes=['NonExistentType'],
                compute_effect_size=False
            )
    
    def test_nsimplex_single_target_type(self, sample_data, temp_output_dir):
        """Test n-simplex analysis with single target cell type."""
        neighbor_matrix, global_log_odds = n_wise_logOdds(
            spatial_obj=sample_data,
            out_dir=temp_output_dir,
            label='test_single_target',
            target_celltypes=['TypeA'],
            compute_effect_size=False
        )
        
        assert isinstance(neighbor_matrix, pd.DataFrame)
        assert isinstance(global_log_odds, (float, np.float64))
        # 3 reference types vs 1 target type
        assert neighbor_matrix.shape == (3, 1)
    
    def test_nsimplex_output_files_content(self, sample_data, temp_output_dir):
        """Test the content of n-simplex output files."""
        target_types = ['TypeA', 'TypeB']
        
        n_wise_logOdds(
            spatial_obj=sample_data,
            out_dir=temp_output_dir,
            label='test_content',
            target_celltypes=target_types
        )
        
        # Load and check neighbor matrix (saved as logOdds_matrix for n-simplex)
        neighbor_matrix = pd.read_csv(
            os.path.join(temp_output_dir, 'test_content-logOdds_matrix.csv'), 
            index_col=0
        )
        assert neighbor_matrix.shape == (3, 2)
        assert not neighbor_matrix.isnull().any().any()  # No NaN values
        
        # Load and check probabilities matrix
        probs = pd.read_csv(
            os.path.join(temp_output_dir, 'test_content-probabilities_matrix.csv'),
            index_col=0
        )
        assert probs.shape == (3, 2)
        assert not probs.isnull().any().any()
        assert (probs >= 0).all().all()  # All probabilities should be non-negative
        assert (probs <= 1).all().all()  # All probabilities should be <= 1
    
    def test_nsimplex_log_odds_calculation(self, sample_data, temp_output_dir):
        """Test that global log-odds calculation produces reasonable results."""
        # Use all three types for comprehensive n-simplex calculation
        target_types = ['TypeA', 'TypeB', 'TypeC']
        
        neighbor_matrix, global_log_odds = n_wise_logOdds(
            spatial_obj=sample_data,
            out_dir=temp_output_dir,
            label='test_log_odds',
            target_celltypes=target_types,
            compute_effect_size=False
        )
        
        # Global log-odds should be finite
        assert np.isfinite(global_log_odds)
        
        # For spatially separated clusters, we might expect negative log-odds
        # (less interaction than expected by chance), but this depends on parameters
        assert isinstance(global_log_odds, (float, np.float64))
