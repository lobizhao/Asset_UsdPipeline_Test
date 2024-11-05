import os
from pxr import Usd, UsdShade, Sdf, UsdGeom, Gf


# USD 生成器类，用于创建材质和模型绑定
class USDGenerator:
    def __init__(self, stage, prim_name="Root"):
        self.stage = stage
        self.prim_path = f"/{prim_name}"
        self.root_prim = stage.DefinePrim(self.prim_path, "Xform")
        self.looks_scope = stage.DefinePrim(f"{self.prim_path}/Looks", "Scope")

    def create_material(self, material_name):
        """创建材质并返回基础着色器"""
        self.material_path = f"{self.prim_path}/Looks/{material_name}"
        self.material = UsdShade.Material.Define(self.stage, self.material_path)
        shader_path = f"{self.material_path}/Shader"
        shader = UsdShade.Shader.Define(self.stage, shader_path)
        shader.CreateIdAttr("UsdPreviewSurface")
        return shader

    def create_texture_shader(self, texture_path, shader_name, default_color=Gf.Vec3f(1.0, 1.0, 1.0)):
        """根据类型创建纹理着色器"""
        texture_shader = UsdShade.Shader.Define(self.stage, f"{self.material_path}/{shader_name}_Texture")
        texture_shader.CreateIdAttr("UsdUVTexture")
        if texture_path:
            texture_shader.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(texture_path)
        else:
            texture_shader.CreateInput("fallback", Sdf.ValueTypeNames.Float3).Set(default_color)

        # 根据 shader 类型创建输出
        if shader_name == "Diffuse":
            texture_shader.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
        elif shader_name == "MetallicRoughness":
            texture_shader.CreateOutput("b", Sdf.ValueTypeNames.Float)  # metallic
            texture_shader.CreateOutput("g", Sdf.ValueTypeNames.Float)  # roughness
        elif shader_name == "Normal":
            texture_shader.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)  # normal
        return texture_shader

    def setup_material_with_textures(self, material_name, diffuse_path, mr_path, normal_path):
        """设置材质并绑定纹理到对应的着色器输入"""
        shader = self.create_material(material_name)

        # 创建并连接纹理着色器
        diffuse_texture = self.create_texture_shader(diffuse_path, "Diffuse")
        mr_texture = self.create_texture_shader(mr_path, "MetallicRoughness")
        normal_texture = self.create_texture_shader(normal_path, "Normal")

        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Float3).ConnectToSource(diffuse_texture.GetOutput("rgb"))
        shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).ConnectToSource(mr_texture.GetOutput("b"))
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).ConnectToSource(mr_texture.GetOutput("g"))
        shader.CreateInput("normal", Sdf.ValueTypeNames.Float3).ConnectToSource(normal_texture.GetOutput("rgb"))

        # 设置材质表面输出
        self.material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")

    def add_mesh_with_material_binding(self, model_usd_path):
        """添加模型并绑定材质"""
        mesh = self.stage.DefinePrim(f"{self.prim_path}", "Xform")
        mesh.GetReferences().AddReference(model_usd_path)

        # 转换模型到右手坐标系
        xformable = UsdGeom.Xformable(mesh)
        xformable.AddRotateXYZOp().Set(Gf.Vec3f(-90.0, 0.0, 0.0))
        xformable.AddScaleOp().Set(Gf.Vec3f(1000.0, 1000.0, 1000.0))
        UsdShade.MaterialBindingAPI(mesh).Bind(self.material)


# 文件处理类，用于验证和组织材质文件
class FileProcessor:
    suffix_to_type = {
        '_base.usd': 'mesh',
        '_texture_diff.png': 'diff',
        '_texture_MR.png': 'mr',
        '_texture_normal.png': 'normal'
        #'_mat.usd': 'mat'
    }

    def __init__(self, directory_path):
        self.directory_path = directory_path
        self.assets = {}

    def check_directory(self):
        if not os.path.isdir(self.directory_path):
            print("目录不存在，请检查路径是否正确")
            return False
        return True

    def process_files(self):
        type_names = set(self.suffix_to_type.values())

        for filename in os.listdir(self.directory_path):
            for suffix, file_type in self.suffix_to_type.items():
                if filename.endswith(suffix):
                    name = filename[:-len(suffix)]

                    if name not in self.assets:
                        self.assets[name] = {type_name: '' for type_name in type_names}

                    self.assets[name][file_type] = filename
                    break

    def validate_assets(self):
        """检查每个前缀是否包含所有所需的文件后缀，如果缺失则打印完整的缺失文件名"""
        missing_elements = False

        for name, file_types in self.assets.items():
            for suffix, file_type in self.suffix_to_type.items():
                if not file_types[file_type]:  # 检查文件类型是否存在
                    missing_elements = True
                    print(f"Prefix '{name}' is missing the file: '{name}{suffix}'")

        if not missing_elements:
            print("所有文件都已齐全。")

    def display_assets(self):
        for name, file_types in self.assets.items():
            print(f'----- {name} -----')
            for file_type, file_name in file_types.items():
                print(f'{file_type:<10}: {file_name}')
            print()


def generate_usd_from_folder(folder_path):
    file_processor = FileProcessor(folder_path)

    if not file_processor.check_directory():
        return

    file_processor.process_files()
    file_processor.display_assets()
    file_processor.validate_assets()

    for prefix, file_paths in file_processor.assets.items():
        output_file = os.path.join(folder_path, f"{prefix}_final.usd")
        stage = Usd.Stage.CreateNew(output_file)
        usd_generator = USDGenerator(stage, prim_name=prefix)

        usd_generator.setup_material_with_textures(
            material_name=prefix,
            diffuse_path=os.path.join(folder_path, file_paths.get("diff")),
            mr_path=os.path.join(folder_path, file_paths.get("mr")),
            normal_path=os.path.join(folder_path, file_paths.get("normal"))
        )

        usd_generator.add_mesh_with_material_binding(model_usd_path=os.path.join(folder_path, file_paths["mesh"]))
        stage.GetRootLayer().Save()

        print(f"USD file '{output_file}' created.")


# 固定的目录路径
folder_path = r"D:\Asset_Pipeline_Test\Assets"
generate_usd_from_folder(folder_path)
