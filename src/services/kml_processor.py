import xml.etree.ElementTree as ET
import pandas as pd
from geopy.distance import geodesic
import zipfile
import os
import json
from pathlib import Path

class KMLDataProcessor:
    def __init__(self, file_path):
        """
        Initialize the data processor with KML/KMZ data from Google My Maps
        """
        self.file_path = file_path
        self.route_segments = []
        self.complete_route = []
        self.stops = []
        self.total_distance = 0
        self.segment_distances = []
        
    def _extract_kml_from_kmz(self, kmz_path):
        """
        Extract KML content from KMZ file
        """
        with zipfile.ZipFile(kmz_path, 'r') as kmz:
            # Look for the main KML file (usually doc.kml or the first .kml file)
            kml_files = [f for f in kmz.namelist() if f.endswith('.kml')]
            
            if not kml_files:
                raise ValueError("No KML files found in KMZ archive")
            
            # Usually the main file is doc.kml, otherwise take the first one
            main_kml = 'doc.kml' if 'doc.kml' in kml_files else kml_files[0]
            
            # Extract and return the KML content
            with kmz.open(main_kml) as kml_file:
                return kml_file.read().decode('utf-8')
    
    def parse_kml(self):
        """
        Parse KML/KMZ file to extract route segments and stops
        """
        # Determine if file is KMZ or KML
        if self.file_path.suffix == '.kmz':
            kml_content = self._extract_kml_from_kmz(self.file_path)
            root = ET.fromstring(kml_content)
        elif self.file_path.suffix == '.kml':
            tree = ET.parse(self.file_path)
            root = tree.getroot()
        else:
            raise ValueError("File must be either .kml or .kmz format")
        
        # Handle KML namespace
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        # Find all placemarks
        placemarks = root.findall('.//kml:Placemark', ns)
        
        for placemark in placemarks:
            name = placemark.find('kml:name', ns)
            name_text = name.text if name is not None else "Unknown"
            
            # Check for LineString (route segments)
            linestring = placemark.find('.//kml:LineString/kml:coordinates', ns)
            if linestring is not None:
                coords = self._parse_coordinates(linestring.text)
                self.route_segments.append({
                    'name': name_text,
                    'coordinates': coords,
                    'distance': self._calculate_segment_distance(coords)
                })
            
            # Check for Point (stops)
            point = placemark.find('.//kml:Point/kml:coordinates', ns)
            if point is not None:
                coords = self._parse_coordinates(point.text)[0]  # Points have single coordinate
                if "France" not in name_text:
                    self.stops.append({
                        'name': name_text,
                        'coordinates': coords
                    })
        
        # Calculate total distance and segment distances
        self.total_distance = sum(seg['distance'] for seg in self.route_segments)
        self.segment_distances = [seg['distance'] for seg in self.route_segments]
        
        print(f"Parsed {len(self.route_segments)} route segments")
        print(f"Parsed {len(self.stops)} stops")
        print(f"Total route distance: {self.total_distance:.2f} km")
        
        # Merge route segments into one complete route
        self.merge_route_segments()
        
    def merge_route_segments(self):
        """
        Merge all route segments into one complete route by connecting them properly
        """
        if not self.route_segments:
            return
        
        print(f"\n=== MERGING ROUTE SEGMENTS ===")
        
        # Start with the first segment
        merged_coordinates = []
        
        # Sort segments by name to ensure proper order (part 1, part 2, etc.)
        sorted_segments = sorted(self.route_segments, key=lambda x: x['name'])
        
        for i, segment in enumerate(sorted_segments):
            segment_coords = segment['coordinates']
            print(f"Processing segment {i+1}: '{segment['name']}' ({len(segment_coords)} points, {segment['distance']:.2f} km)")
            
            if i == 0:
                # First segment - add all coordinates
                merged_coordinates.extend(segment_coords)
                print(f"  Added all {len(segment_coords)} coordinates from first segment")
            else:
                # For subsequent segments, check if we need to connect them
                last_coord = merged_coordinates[-1]
                first_coord = segment_coords[0]
                
                # Calculate distance between last point of merged route and first point of current segment
                gap_distance = geodesic(last_coord, first_coord).kilometers
                print(f"  Gap distance to next segment: {gap_distance:.3f} km")
                
                if gap_distance < 0.1:  # If very close (< 100m), consider connected
                    # Skip the first coordinate to avoid duplication
                    merged_coordinates.extend(segment_coords[1:])
                    print(f"  Segments are connected, added {len(segment_coords)-1} new coordinates")
                else:
                    # If there's a gap, add all coordinates (creating a straight line connection)
                    merged_coordinates.extend(segment_coords)
                    print(f"  Gap detected, added all {len(segment_coords)} coordinates (total gap: {gap_distance:.3f} km)")
        
        # Store the complete merged route
        self.complete_route = merged_coordinates
        
        # Recalculate total distance for the merged route
        merged_distance = self._calculate_segment_distance(merged_coordinates)
        
        print(f"\n=== MERGE COMPLETE ===")
        print(f"Original segments distance: {self.total_distance:.2f} km")
        print(f"Merged route distance: {merged_distance:.2f} km")
        print(f"Total coordinates in merged route: {len(merged_coordinates)}")
        
        # Update total distance to reflect the merged route
        self.total_distance = merged_distance
        
    def _parse_coordinates(self, coord_string):
        """Parse coordinate string from KML"""
        coords = []
        for line in coord_string.strip().split():
            if line:
                parts = line.split(',')
                if len(parts) >= 2:
                    lon, lat = float(parts[0]), float(parts[1])
                    coords.append((lat, lon))  # (lat, lon) for geopy
        return coords
    
    def get_complete_route(self):
        """
        Get the complete merged route coordinates
        """
        return self.complete_route
    
    def export_complete_route_summary(self):
        """
        Export summary of the complete route
        """
        if not self.complete_route:
            print("No complete route available. Run parse_kml() first.")
            return None
        
        return {
            'total_coordinates': len(self.complete_route),
            'total_distance_km': self.total_distance,
            'start_coordinate': self.complete_route[0],
            'end_coordinate': self.complete_route[-1],
            'original_segments': len(self.route_segments)
        }
    
    def export_complete_route_to_csv(self, filename='complete_route.csv', base_path='.'):
        """
        Export the complete merged route to a CSV file
        """
        if not self.complete_route:
            print("No complete route available. Run parse_kml() first.")
            return False
        
        # Create DataFrame with route coordinates
        route_data = []
        cumulative_distance = 0
        
        for i, coord in enumerate(self.complete_route):
            if i > 0:
                # Calculate cumulative distance
                prev_coord = self.complete_route[i-1]
                segment_dist = geodesic(prev_coord, coord).kilometers
                cumulative_distance += segment_dist
            
            route_data.append({
                'point_number': i + 1,
                'latitude': coord[0],
                'longitude': coord[1],
                'cumulative_distance_km': cumulative_distance
            })
        
        # Create DataFrame and export
        df = pd.DataFrame(route_data)
        df.to_csv(os.path.join(base_path, filename), index=False)
        
        print(f"Complete route exported to '{filename}'")
        print(f"File contains {len(route_data)} coordinate points")
        return True
    
    def _calculate_segment_distance(self, coordinates):
        """Calculate distance of a coordinate sequence in km"""
        if len(coordinates) < 2:
            return 0
        
        total_dist = 0
        for i in range(len(coordinates) - 1):
            total_dist += geodesic(coordinates[i], coordinates[i+1]).kilometers
        return total_dist


# Example usage
if __name__ == "__main__":
    # Initialize data processor (works with both .kml and .kmz files)
    base_path = Path(__file__).resolve().parent.parent.parent / 'data'
    file_path = base_path / 'Medoc Marathon 2025.kmz'
    processor = KMLDataProcessor(file_path)
    
    # Parse the KML/KMZ file
    processor.parse_kml()
    
    # Show complete route summary
    route_summary = processor.export_complete_route_summary()
    print(f"\n=== COMPLETE ROUTE SUMMARY ===")
    for key, value in route_summary.items():
        print(f"{key}: {value}")
    
    # Get the complete route coordinates
    complete_route = processor.get_complete_route()
    print(f"\nComplete route has {len(complete_route)} coordinate points")
    print(f"First 5 coordinates: {complete_route[:5]}")
    print(f"Last 5 coordinates: {complete_route[-5:]}")
    
    # Export the complete route to CSV
    print(f"\n=== EXPORTING COMPLETE ROUTE ===")
    processor.export_complete_route_to_csv('medoc_marathon_complete_route.csv', base_path)

    # Show all parsed stops
    print(f"\n=== PARSED STOPS ===")
    print(json.dumps({"stops": processor.stops}, indent=4))