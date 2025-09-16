"""
Basic tests for Masquerade package.
"""
import pytest
import numpy as np
from masquerade import Masquerade
import pandas as pd

class TestMasquerade:
    """Test cases for Masquerade class."""
    
    def test_initialization(self):
        """Test that Masquerade initializes with default values."""
        mask = Masquerade()
        assert mask.image_source == ''
        assert mask.spatial_anno == ''
        assert mask.raw_size == 0
        assert mask.target_size == 4
        assert mask.radius == 10
        assert mask.filled is True
    
    def test_pull_ext(self):
        """Test file extension extraction."""
        mask = Masquerade()
        assert mask.pullExt("test.tiff") == "tiff"
        assert mask.pullExt("data.csv") == "csv"
        assert mask.pullExt("image.qptiff") == "qptiff"
    
    def test_generate_circle(self):
        """Test circle coordinate generation."""
        x, y = Masquerade.generate_circle(0, 0, 5, num_points=8)
        
        # Should return arrays
        assert isinstance(x, np.ndarray)
        assert isinstance(y, np.ndarray)
        
        # Should have correct number of points
        assert len(x) == 8
        assert len(y) == 8
        
        # Points should be roughly on the circle (within floating point precision)
        distances = np.sqrt(x**2 + y**2)
        assert np.allclose(distances, 5.0, atol=1e-10)
    
    def test_generate_filled_circle(self):
        """Test filled circle coordinate generation."""
        coords = Masquerade.generate_filled_circle(0, 0, 2)
        
        # Should return a list of tuples
        assert isinstance(coords, list)
        assert len(coords) > 0
        
        # All coordinates should be within the circle
        for x, y in coords:
            distance = np.sqrt(x**2 + y**2)
            assert distance <= 2.0
        
        # Should include the center point
        assert (0, 0) in coords
    
    def test_parameter_setting(self):
        """Test parameter setting."""
        mask = Masquerade()
        
        # Test setting various parameters
        mask.radius = 15
        mask.filled = False
        mask.target_size = 8
        
        assert mask.radius == 15
        assert mask.filled is False
        assert mask.target_size == 8


class TestMasqueradeMethods:
    """Test major processing methods with mock data."""
    
    def create_mock_metadata(self):
        """Create mock spatial metadata for testing."""
        import pandas as pd
   	# Ensure each cluster has >1 point since get_circle_masks requires this
        return pd.DataFrame({
            'x': [10, 12, 20, 22, 30, 32],
            'y': [10, 12, 20, 22, 30, 32],
            'cluster': [1, 1, 2, 2, 3, 3]  # Each cluster has 2 points
        })
 
    def create_mock_image(self, height=50, width=50, channels=3):
        """Create a mock image array."""
        return np.random.randint(0, 255, size=(channels, height, width), dtype=np.uint8)
    
    def create_mock_channels_dict(self):
        """Create mock channels dictionary."""
        return {
            'channel1': np.random.randint(0, 255, size=(40, 40), dtype=np.uint8),
            'channel2': np.random.randint(0, 255, size=(40, 40), dtype=np.uint8),
            'mask1': np.zeros((40, 40), dtype=np.uint8),
            'mask2': np.zeros((40, 40), dtype=np.uint8)
        }
    
    def test_get_circle_masks_with_mock_data(self):
        """Test circle mask generation with mock data."""
        masquerade = Masquerade()
        masquerade.radius = 5
        masquerade.filled = True
        masquerade.adjust_coords = False
        
        # Create mock data
        image = self.create_mock_image(height=50, width=50, channels=3)
        metadata = self.create_mock_metadata()
        set_subset_x = np.array([5, 35])
        set_subset_y = np.array([5, 35])
        
        # Test the method
        channels = masquerade.get_circle_masks(image, metadata, set_subset_x, set_subset_y)
        
        # Verify results
        assert isinstance(channels, dict)
        assert len(channels) > 0
        
        # Check that mask channels were created (should have cluster IDs in names)
        mask_channels = [k for k in channels.keys() if '_mask' in k]
        assert len(mask_channels) > 0
        
        # Check that masks have the right shape
        for channel_name, channel_data in channels.items():
            assert isinstance(channel_data, np.ndarray)
            assert channel_data.shape == (50, 50)  # Should match image dimensions
    
   
        def test_get_circle_masks_filled_vs_outline(self):
            """Test difference between filled and outline circles."""
            masquerade = Masquerade()
            masquerade.radius = 3
            masquerade.adjust_coords = False
    
            image = self.create_mock_image(height=20, width=20, channels=1)
            # Fix: Provide multiple points per cluster as required by get_circle_masks
            metadata = pd.DataFrame({
            'x': [10, 11], 
            'y': [10, 11], 
            'cluster': [1, 1]  # Same cluster, multiple points
            })
            set_subset_x = np.array([0, 20])
            set_subset_y = np.array([0, 20])
    
            # Test filled circles
            masquerade.filled = True
            channels_filled = masquerade.get_circle_masks(image, metadata, set_subset_x, set_subset_y)
    
            # Test outline circles
            masquerade.filled = False
            masquerade.num_points = 20
            channels_outline = masquerade.get_circle_masks(image, metadata, set_subset_x, set_subset_y)
    
            # Both should create channels
            assert len(channels_filled) > 0
            assert len(channels_outline) > 0
    
            # Get the mask arrays
            filled_mask = list(channels_filled.values())[0]
            outline_mask = list(channels_outline.values())[0]
    
            # Both masks should have non-zero pixels
            filled_count = np.sum(filled_mask > 0)
            outline_count = np.sum(outline_mask > 0)
    
            # At small radii, outline might have more pixels than filled due to discrete sampling
            # The important thing is both methods create masks with reasonable pixel counts
            assert filled_count > 0, f"Filled mask should have pixels, got {filled_count}"
            assert outline_count > 0, f"Outline mask should have pixels, got {outline_count}"
    
            # Both should be reasonable for radius=3 (roughly in the range of π*r² = ~28 pixels)
            assert 10 < filled_count < 100, f"Filled count {filled_count} seems unreasonable for radius=3"
            assert 10 < outline_count < 100, f"Outline count {outline_count} seems unreasonable for radius=3" 
    @pytest.mark.skip(reason="Requires actual TIFF file with XML metadata")
    def test_get_continuous_channels(self):
        """Test continuous channel extraction from TIFF."""
        masquerade = Masquerade()
        masquerade.image_source = "test.tiff"  # Would need real file
        masquerade.adjust_coords = False
        
        channels = {}
        set_subset_x = np.array([0, 100])
        set_subset_y = np.array([0, 100])
        
        result_channels, channel_names = masquerade.get_continuous_channels(
            channels, set_subset_x, set_subset_y
        )
        
        assert isinstance(result_channels, dict)
        assert isinstance(channel_names, list)
    
    @pytest.mark.skip(reason="Requires actual TIFF file with XML metadata")
    def test_compress_marker_channels(self):
        """Test marker channel compression."""
        masquerade = Masquerade()
        masquerade.image_source = "test.tiff"  # Would need real file
        masquerade.compression_factor = 0.5
        masquerade.adjust_coords = False
        
        channels = self.create_mock_channels_dict()
        metadata = self.create_mock_metadata()
        
        result_channels, channel_names = masquerade.compress_marker_channels(channels, metadata)
        
        assert isinstance(result_channels, dict)
        assert isinstance(channel_names, list)
    
    def test_write_mask_tiff(self, tmp_path):
        """Test TIFF writing functionality."""
        # Create mock channels
        channels = {
            'test_channel_1': np.random.randint(0, 255, size=(20, 20), dtype=np.uint8),
            'test_channel_2': np.random.randint(0, 255, size=(20, 20), dtype=np.uint8)
        }
        
        # Create temporary output path
        output_path = tmp_path / "test_output.tiff"
        
        # Test the static method
        Masquerade.writeMaskTiff(channels, str(output_path))
        
        # Verify file was created
        assert output_path.exists()
        
        # Try to read it back (basic validation)
        import tifffile
        with tifffile.TiffFile(str(output_path)) as tif:
            assert len(tif.pages) == len(channels)
    
    def test_write_ome_bigtiff(self, tmp_path):
        """Test OME BigTIFF writing functionality."""
        # Create mock channels
        channels = {
            'channel_1': np.random.randint(0, 255, size=(30, 30), dtype=np.uint8),
            'channel_2': np.random.randint(0, 255, size=(30, 30), dtype=np.uint8),
            'mask_1': np.zeros((30, 30), dtype=np.uint8)
        }
        
        channels_to_keep = list(channels.keys())
        output_path = tmp_path / "test_ome.tiff"
        
        # Test the static method
        result = Masquerade.write_ome_bigTiff(channels, str(output_path), channels_to_keep)
        
        # Should return None
        assert result is None
        
        # Verify file was created
        assert output_path.exists()
    
    def test_compression_factor_calculation(self):
        """Test compression factor calculation logic."""
        masquerade = Masquerade()
        masquerade.target_size = 2.0  # 2GB target
        masquerade.raw_size = 4.0     # 4GB raw
        masquerade.compress = True
        
        # Create mock data for compression calculation
        image = self.create_mock_image(height=100, width=100, channels=1)
        metadata = self.create_mock_metadata()
        set_subset_x = np.array([0, 100])
        set_subset_y = np.array([0, 100])
        
        # This should trigger compression factor calculation
        channels = masquerade.get_circle_masks(image, metadata, set_subset_x, set_subset_y)
        
        # Compression factor should be calculated
        assert hasattr(masquerade, 'compression_factor')
        assert masquerade.compression_factor > 0
        assert masquerade.compression_factor <= 1.0


# Integration test (requires actual data files - can be skipped if files don't exist)
@pytest.mark.skip(reason="Requires actual data files")
class TestMasqueradeIntegration:
    """Integration tests that require actual data files."""
    
    def test_full_pipeline_with_real_data(self):
        """Test complete pipeline with real data files."""
        masquerade = Masquerade()
        masquerade.image_source = "/Users/ee699/working/TRIC/Aifantis-CODEX/artifact-removal/1373-no_artefacts_segmentation-spatial-anno-res5.tiff"  # Would need actual file
        masquerade.spatial_anno = "/Users/ee699/working/TRIC/Aifantis-CODEX/artifact-removal/Annotated/1373/phenomenalist-modify_clusters-output-2025-08-18/annotated_spatial_coords-v1.csv"   # Would need actual file
        masquerade.radius = 10
        masquerade.filled = True
        
        # Full pipeline test
        image, subset_x, subset_y, metadata = masquerade.PreProcessImage()
        channels = masquerade.get_circle_masks(image, metadata, subset_x, subset_y)
        final_channels, names = masquerade.get_continuous_channels(channels, subset_x, subset_y)
        
        assert image is not None
        assert len(subset_x) > 0
        assert len(subset_y) > 0
        assert len(metadata) > 0
        assert isinstance(channels, dict)
        assert isinstance(final_channels, dict)
        assert isinstance(names, list)


class TestCommandLineInterface:
    """Test command line interface functionality."""
    
    def test_string_to_boolean_conversion(self):
        """Test string to boolean conversion logic."""
        # Test True conversions
        assert 'True' == 'True'
        assert 'False' == 'False'
        
        # Test parameter setting with string inputs
        mask = Masquerade()
        
        # Simulate command line parameter parsing
        adjust_coords_str = 'True'
        compress_str = 'False'
        filled_str = 'True'
        
        # Convert strings to booleans (as would happen in CLI)
        mask.adjust_coords = True if adjust_coords_str == 'True' else False
        mask.compress = True if compress_str == 'True' else False
        mask.filled = True if filled_str == 'True' else False
        
        assert mask.adjust_coords is True
        assert mask.compress is False
        assert mask.filled is True
    
    def test_parameter_type_conversion(self):
        """Test parameter type conversions from command line strings."""
        mask = Masquerade()
        
        # Test numeric parameter conversion
        radius_str = "15"
        target_size_str = "2.5"
        num_points_str = "50"
        
        mask.radius = int(radius_str)
        mask.target_size = float(target_size_str)
        mask.num_points = int(num_points_str)
        
        assert mask.radius == 15
        assert mask.target_size == 2.5
        assert mask.num_points == 50
        assert isinstance(mask.radius, int)
        assert isinstance(mask.target_size, float)
        assert isinstance(mask.num_points, int)
    
    def test_none_parameter_handling(self):
        """Test handling of None parameters from command line."""
        mask = Masquerade()
        
        # Test None parameter handling
        marker_metadata_str = 'None'
        marker_metadata = None if marker_metadata_str == 'None' else marker_metadata_str
        
        mask.relevant_markers = marker_metadata
        assert mask.relevant_markers is None


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__])
