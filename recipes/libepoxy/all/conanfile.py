from conans import ConanFile, Meson, tools
import os
import shutil


class EpoxyConan(ConanFile):
    name = "libepoxy"
    description = "libepoxy is a library for handling OpenGL function pointer management"
    topics = ("conan", "libepoxy", "opengl")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/anholt/libepoxy"
    license = "MIT"
    generators = "pkg_config"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "glx": [True, False],
        "egl": [True, False],
        "x11": [True, False]
    }
    default_options = {
        "shared": True,
        "fPIC": True,
        "glx": True,
        "egl": False,
        "x11": True
    }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd
        if self.settings.os == "Windows":
            self.options.shared = True

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.os != "Linux":
            del self.options.glx
            del self.options.egl
            del self.options.x11

    def build_requirements(self):
        self.build_requires("meson/0.54.2")

    def requirements(self):
        self.requires("opengl/system")
        if self.settings.os == "Linux":
            if self.options.x11:
                self.requires("xorg/system")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_meson(self):
        meson = Meson(self)
        defs = {}
        defs["docs"] = "false"
        defs["tests"] = "false"
        for opt in ["glx", "egl"]:
            defs[opt] = "yes" if self.settings.os == "Linux" and getattr(self.options, opt) else "no"
        for opt in ["x11"]:
            defs[opt] = "true" if self.settings.os == "Linux" and getattr(self.options, opt) else "false"
        args=[]
        args.append("--wrap-mode=nofallback")
        meson.configure(defs=defs, build_folder=self._build_subfolder, source_folder=self._source_subfolder, pkg_config_paths=[self.install_folder], args=args)
        return meson

    def build(self):
        for package in self.deps_cpp_info.deps:
            lib_path = self.deps_cpp_info[package].rootpath
            for dirpath, _, filenames in os.walk(lib_path):
                for filename in filenames:
                    if filename.endswith(".pc"):
                        if filename in ["cairo.pc", "fontconfig.pc", "xext.pc", "xi.pc", "x11.pc", "xcb.pc"]:
                            continue
                        shutil.copyfile(os.path.join(dirpath, filename), filename)
                        tools.replace_prefix_in_pc_file(filename, lib_path)
        with tools.environment_append(tools.RunEnvironment(self).vars):
            meson = self._configure_meson()
            meson.build()

    def package(self):
        self.copy(pattern="COPYING", dst="licenses", src=self._source_subfolder)
        meson = self._configure_meson()
        meson.install()
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.libs = ["epoxy"]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["dl"]
        self.cpp_info.names["pkg_config"] = "epoxy"

