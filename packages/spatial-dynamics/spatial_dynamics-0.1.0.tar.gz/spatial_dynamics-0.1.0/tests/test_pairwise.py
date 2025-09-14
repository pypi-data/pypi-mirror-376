"""Tests for pairwise analysis functionality."""

import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from spatial_dynamics import pairwise_logOdds


class TestPairwiseLogOdds:
    """Test class for pairwise log-odds analysis."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample spatial data for testing."""
        np.random.seed(42)
        n_cells = 100
        
        # Create two clusters of cells
        cluster1_x = np.random.normal(20, 5, n_cells // 2)
        cluster1_y = np.random.normal(20, 5, n_cells // 2)
        cluster1_type = ['TypeA'] * (n_cells // 2)
        
        cluster2_x = np.random.normal(80, 5, n_cells // 2)
        cluster2_y = np.random.normal(80, 5, n_cells // 2)
        cluster2_type = ['TypeB'] * (n_cells // 2)
        
        data = pd.DataFrame({
            'x': np.concatenate([cluster1_x, cluster2_x]),
            'y': np.concatenate([cluster1_y, cluster2_y]),
            'cluster': cluster1_type + cluster2_type
        })
        
        return data
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory for test outputs."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup is handled by tempfile
    
    def test_basic_pairwise_analysis(self, sample_data, temp_output_dir):
        """Test basic pairwise log-odds calculation."""
        result = pairwise_logOdds(
            spatial_obj=sample_data,
            out_dir=temp_output_dir,
            label='test',
            compute_effect_size=False
        )
        
        # Check return type and structure
        assert isinstance(result, pd.DataFrame)
        assert result.shape == (2, 2)  # 2 cell types
        assert all(col in ['TypeA', 'TypeB'] for col in result.columns)
        assert all(idx in ['TypeA', 'TypeB'] for idx in result.index)
        
        # Check output files exist
        assert os.path.exists(os.path.join(temp_output_dir, 'test-logOdds_matrix.csv'))
        assert os.path.exists(os.path.join(temp_output_dir, 'test-probabilities_matrix.csv'))
    
    def test_pairwise_with_effect_sizes(self, sample_data, temp_output_dir):
        """Test pairwise analysis with effect size computation."""
        result = pairwise_logOdds(
            spatial_obj=sample_data,
            out_dir=temp_output_dir,
            label='test_effects',
            compute_effect_size=True
        )
        
        # Check basic structure
        assert isinstance(result, pd.DataFrame)
        assert result.shape == (2, 2)
        
        # Check effect sizes file exists
        assert os.path.exists(os.path.join(temp_output_dir, 'test_effects-KS-effect_sizes_matrix.csv'))
        
        # Load and check effect sizes file
        effect_sizes = pd.read_csv(os.path.join(temp_output_dir, 'test_effects-KS-effect_sizes_matrix.csv'), index_col=0)
        assert effect_sizes.shape == (2, 2)
    
    def test_custom_parameters(self, sample_data, temp_output_dir):
        """Test pairwise analysis with custom parameters."""
        result = pairwise_logOdds(
            spatial_obj=sample_data,
            out_dir=temp_output_dir,
            label='test_custom',
            resolution=0.5,
            p1=5,
            p2=25,
            compute_effect_size=False
        )
        
        assert isinstance(result, pd.DataFrame)
        assert result.shape == (2, 2)
    
    def test_invalid_input_data(self, temp_output_dir):
        """Test handling of invalid input data."""
        # Missing required columns
        invalid_data = pd.DataFrame({
            'x': [1, 2, 3],
            'y': [1, 2, 3]
            # Missing 'cluster' column
        })
        
        with pytest.raises(KeyError):
            pairwise_logOdds(
                spatial_obj=invalid_data,
                out_dir=temp_output_dir,
                label='test_invalid'
            )
    
    def test_single_cell_type(self, temp_output_dir):
        """Test behavior with single cell type."""
        single_type_data = pd.DataFrame({
            'x': [1, 2, 3, 4, 5],
            'y': [1, 2, 3, 4, 5],
            'cluster': ['TypeA'] * 5
        })
        
        result = pairwise_logOdds(
            spatial_obj=single_type_data,
            out_dir=temp_output_dir,
            label='test_single'
        )
        
        assert isinstance(result, pd.DataFrame)
        assert result.shape == (1, 1)
    
    def test_output_files_content(self, sample_data, temp_output_dir):
        """Test the content of output files."""
        pairwise_logOdds(
            spatial_obj=sample_data,
            out_dir=temp_output_dir,
            label='test_content'
        )
        
        # Load and check log-odds matrix
        log_odds = pd.read_csv(os.path.join(temp_output_dir, 'test_content-logOdds_matrix.csv'), index_col=0)
        assert log_odds.shape == (2, 2)
        assert not log_odds.isnull().any().any()  # No NaN values
        
        # Load and check probabilities matrix
        probs = pd.read_csv(os.path.join(temp_output_dir, 'test_content-probabilities_matrix.csv'), index_col=0)
        assert probs.shape == (2, 2)
        assert not probs.isnull().any().any()
        assert (probs >= 0).all().all()  # All probabilities should be non-negative
        assert (probs <= 1).all().all()  # All probabilities should be <= 1
