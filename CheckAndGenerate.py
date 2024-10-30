import os
from pxr import Usd, UsdShade, Sdf, UsdGeom, Gf
#reference : https://docs.omniverse.nvidia.com/dev-guide/latest/programmer_ref/usd/materials/create-mdl-material.html
class USDGenerator:
    def __init__(self, stage, prim_name="Root"):
        self.stage = stage
        self.prim_path = f"/{prim_name}"
        self.root_prim = stage.DefinePrim(self.prim_path, "Xform")
        self.looks_scope = stage.DefinePrim(f"{self.prim_path}/Looks", "Scope")

    def create_material(self, material_name):
        self.material_path = f"{self.prim_path}/Looks/{material_name}"
        self.material = UsdShade.Material.Define(self.stage, self.material_path)
        shader_path = f"{self.material_path}/Shader"
        shader = UsdShade.Shader.Define(self.stage, shader_path)
        shader.CreateIdAttr("UsdPreviewSurface")
        return shader

    def create_texture_shader(self, texture_path, shader_name, default_color=Gf.Vec3f(1.0, 1.0, 1.0)):
        texture_shader = UsdShade.Shader.Define(self.stage, f"{self.material_path}/{shader_name}_Texture")
        texture_shader.CreateIdAttr("UsdUVTexture")
        if texture_path:
            texture_shader.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(texture_path)
        else:
            texture_shader.CreateInput("fallback", Sdf.ValueTypeNames.Float3).Set(default_color)

        # texture_shader.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
        # texture_shader.CreateOutput("b", Sdf.ValueTypeNames.Float)  # metallic channel
        # texture_shader.CreateOutput("g", Sdf.ValueTypeNames.Float)  # roughness channel
        if shader_name == "Diffuse":
            texture_shader.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
        elif shader_name == "MetallicRoughness":
            texture_shader.CreateOutput("b", Sdf.ValueTypeNames.Float)  # metallic
            texture_shader.CreateOutput("g", Sdf.ValueTypeNames.Float)  # roughness
        elif shader_name == "Normal":
            texture_shader.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)  # normal
        return texture_shader

    def setup_material_with_textures(self, material_name,diffuse_path, mr_path, normal_path):
        shader = self.create_material(material_name)
        # 创建纹理着色器
        diffuse_texture = self.create_texture_shader(diffuse_path, "Diffuse")
        mr_texture = self.create_texture_shader(mr_path, "MetallicRoughness")
        normal_texture = self.create_texture_shader(normal_path, "Normal")

        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Float3).ConnectToSource(diffuse_texture.GetOutput("rgb"))
        shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).ConnectToSource(mr_texture.GetOutput("b"))
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).ConnectToSource(mr_texture.GetOutput("g"))
        shader.CreateInput("normal", Sdf.ValueTypeNames.Float3).ConnectToSource(normal_texture.GetOutput("rgb"))

        self.material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")


    def add_mesh_with_material_binding(self, model_usd_path):
        mesh = self.stage.DefinePrim(f"{self.prim_path}/Mesh", "Xform")
        mesh.GetReferences().AddReference(model_usd_path)

        UsdShade.MaterialBindingAPI(mesh).Bind(self.material)


class FileProcessor:
    required_files = ["_base.usd", "_texture_diff.png", "_texture_MR.png", "_texture_normal.png"]
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def get_prefix_files(self):
        files_dict = {}
        for file_name in os.listdir(self.folder_path):
            full_path = os.path.join(self.folder_path, file_name)
            if os.path.isfile(full_path):
                prefix = "_".join(file_name.split("_")[:2])
                if prefix not in files_dict:
                    files_dict[prefix] = []
                files_dict[prefix].append(full_path)
        return files_dict

    def validate_files(self, files_dict):
        valid_prefixes = {}
        for prefix, files in files_dict.items():
            base_usd = next((f for f in files if f.endswith("_base.usd")), None)
            if not base_usd:
                print(f"Prefix '{prefix}' is missing the .usd file. Skipping...")
                continue

            file_paths = {
                "_base.usd": base_usd,
                "_texture_diff.png": next((f for f in files if f.endswith("_texture_diff.png")), None),
                "_texture_MR.png": next((f for f in files if f.endswith("_texture_MR.png")), None),
                "_texture_normal.png": next((f for f in files if f.endswith("_texture_normal.png")), None)
            }

            missing_textures = [name for name, path in file_paths.items() if name.endswith(".png") and not path]
            if missing_textures:
                print(f"Prefix '{prefix}' is missing the following texture files:")
                for missing in missing_textures:
                    print(f" - {missing}")

            valid_prefixes[prefix] = file_paths
        return valid_prefixes


def generate_usd_from_folder(folder_path):
    file_processor = FileProcessor(folder_path)
    files_dict = file_processor.get_prefix_files()
    valid_prefixes = file_processor.validate_files(files_dict)

    for prefix, file_paths in valid_prefixes.items():
        output_file = os.path.join(folder_path, f"{prefix}_MatGeo.usd")
        stage = Usd.Stage.CreateNew(output_file)

        usd_generator = USDGenerator(stage, prim_name=prefix)
        usd_generator.setup_material_with_textures(
            material_name=prefix,
            diffuse_path=file_paths.get("_texture_diff.png"),
            mr_path=file_paths.get("_texture_MR.png"),
            normal_path=file_paths.get("_texture_normal.png")
        )
        usd_generator.add_mesh_with_material_binding(model_usd_path=file_paths["_base.usd"])

        stage.GetRootLayer().Save()
        print(f"USD file '{output_file}' created.")

# input folder path
folder_path = input("Enter the file path: ")
#folder_path = r"D:\Asset_Pipeline_Test\Assets"
generate_usd_from_folder(folder_path)