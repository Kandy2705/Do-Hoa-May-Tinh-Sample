import os
import shutil
import tempfile

def setup_texture():
    # Source path to the texture (using raw string to handle backslashes)
    source_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'texcube', 'image')
    source_path = os.path.join(source_dir, 'texture.jpeg')
    
    # Create a temporary directory with ASCII-only path
    temp_dir = os.path.join(tempfile.gettempdir(), 'texcube_textures')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Destination path in the temp directory
    dest_path = os.path.join(temp_dir, 'texture.jpeg')
    
    # Copy the texture file
    shutil.copy2(source_path, dest_path)
    
    print(f"Texture copied to: {dest_path}")
    return dest_path

if __name__ == "__main__":
    texture_path = setup_texture()
    print(f"Texture is now available at: {texture_path}")
