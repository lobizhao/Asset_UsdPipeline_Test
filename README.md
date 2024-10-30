# Asset_UsdPipeline_Test

# The script contains two main class
- FilePorcessor:  Traversal  the Asset folder, orgnizing the relationships between files using a hashmap, checking for missing files. and print missing file information.

- USDGenertor: Create a new USD file, where each Pirm includes mesh data and materials. The material is nameed is named based on the prefix and automatically links to the corresponding texture paths. 


## Workflow
1. Input the Asset folder path.

2. Traversal the files in the folder to extract each file's prefix. Store files with the same prefix in a hashmap, where the prefix string is the key and all files sharing that prefix are stored as values.
    - def get_prefix_files(): Traverses all files in the folder, extracts file name prefixes, and returns a dictionary where each prefix maps to a list of all files sharing that prefix.

    - validate_files(self, files_dict): Filters file content, determines valid files, checks for missing files, and reports missing information. Finally, returns a list of valid files ready for USD file generation.

    - create_material(self, material_name): Creates a material with the same name as the mesh file and associates it with the required shader configuration.

    - create_texture_shader(self, texture_path, shader_name, default_color=Gf.Vec3f(1.0, 1.0, 1.0)): Creates a texture shader. If the texture path is empty, the shader uses the default_color as a fallback.

    - setup_material_with_textures(self, material_name, diffuse_path, mr_path, normal_path): Associates the material with the corresponding textures and configures the Metallic and Roughness channels.

    - add_mesh_with_material_binding(self, model_usd_path): Adds the mesh resource to the Prim and binds it to the material.


3. Traversal the hashmap to check for missing required files: 
    - If the .usd file is missing and only texture files are found, print the missing file information and skip this set of files.
    - If the .usd file is present but some texture files are missing, print the missing texture information and proceed to create the material. Missing textures will have empty paths and will be filled with a default color vec3(1.0, 1.0, 1.0).
    - Create a new hashmap excluding entries without .usd files, returning only the valid files for USD generation.

4. Iterate over the valid files to create the stage, prim, and material for each prefix.

## Standalone Missing File Check Feature
Before generating new USD files, you can use the file validation feature alone: 
- Call the validate_files method in the FileProcessor class to detect and print all missing asset files. This can help ensure file completeness before actual USD file generation, preventing potential errors.

## Current Issues
- Coordinate System Mismatch: The mesh resource is exported from a left-handed coordinate system tool. Therefore, an additional rotation is required to correctly align the asset in Omniverse.

- Material File Loading Warning: When opening the material file for the first time in “Open in MDL Material Graph,” a console error appears: Traceback (most recent call last): .... However, after a few seconds, the texture node links open normally without any further modification.