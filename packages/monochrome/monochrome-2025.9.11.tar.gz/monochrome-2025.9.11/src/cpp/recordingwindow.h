#pragma once

#include <GLFW/glfw3.h>
#include <utility>

#include "recordingwindow_helpers.h"
#include "utils/colormap.h"

class RecordingWindow;
using SharedRecordingPtr = std::shared_ptr<RecordingWindow>;

class RecordingWindow : public Recording {
 public:
  static inline float scale_fct = 1;

  GLFWwindow *window    = nullptr;
  GLFWwindow *glcontext = nullptr;
  bool active           = true;
  std::vector<SharedRecordingPtr> children;

  RecordingPlaybackCtrl playback;
  Histogram<float, 256> histogram;
  BitRange bitrange       = BitRange::NONE;
  OpacityFunction opacity = OpacityFunction::FIXED_100;
  ExportCtrl export_ctrl;
  std::vector<Trace> traces;
  std::vector<FlowData> flows;                                      // use add_flow() to add members
  std::vector<std::shared_ptr<global::PointsVideo>> points_videos;  // use add_points_video() to add
  struct {
    bool show = false;
    std::string comment;
  } comment_edit_ui;

  RecordingWindow(const fs::path &path) : RecordingWindow(file_factory(path)){};
  RecordingWindow(std::shared_ptr<AbstractFile> file_,
                  Transformations transformation_ = Transformations::None);

  virtual ~RecordingWindow() {
    if (window != nullptr) {
      clear_gl_memory();
      glfwDestroyWindow(window);
      for (auto &child : children) {
        child->glcontext = nullptr;
      }
    }
  }

  virtual void open_window();
  virtual void set_context(GLFWwindow *new_context);

  virtual void display();
  virtual void render();

  virtual void load_next_frame() { load_frame(playback.step()); }

  virtual float &get_min(bool base = false) {
    base = base || (transformation != Transformations::FrameDiff &&
                    transformation != Transformations::ContrastEnhancement);
    if (base) {
      return brightness_min;
    } else {
      return transform_ptr->min;
    }
  }

  virtual float &get_max(bool base = false) {
    base = base || (transformation != Transformations::FrameDiff &&
                    transformation != Transformations::ContrastEnhancement);
    if (base) {
      return brightness_max;
    } else {
      return transform_ptr->max;
    }
  }

  virtual void add_trace(const Vec2i &pos);
  virtual void remove_trace(const Vec2i &pos);

  static void flip_lr() { rotations.flip_ud(); }
  static void flip_ud() { rotations.flip_lr(); }
  static void flip_reset() { rotations.flip_reset(); }
  static void set_rotation(short rotation);
  static void add_rotation(short d_rotation);

  static short get_rotation() { return rotations.get_rotation(); }
  static bool get_flip_lr() { return rotations.get_flip_lr(); }
  static bool get_flip_ud() { return rotations.get_flip_ud(); }

  virtual void colormap(ColorMap cmap);
  ColorMap colormap() const { return cmap_; }
  void clear_color(const ImVec4 &color) {
    if (glcontext != window) return;

    auto w = clear_color_.w;
    clear_color_ = color;
    clear_color_.w = w;
    auto prev_context = glfwGetCurrentContext();
    glfwMakeContextCurrent(window);
    glClearColor(color.x, color.y, color.z, color.w);
    glfwMakeContextCurrent(prev_context);
  }
  ImVec4 clear_color() const { return clear_color_; }
  void fixed_color(const Vec3f &color) {
    fixed_color_ = color;
    colormap(cmap_);
  }
  Vec3f fixed_color() const { return fixed_color_; }


  void set_name(const std::string &new_name) override;
  void resize_window();
  fs::path save_snapshot(std::string output_png_path_template = "");
  void start_recording(const global::ExportVideoCommand &cmd);
  void start_recording(const fs::path &filename, int fps = 30, std::string description = "");
  void stop_recording();

  virtual void set_transformation(Transformations type);
  Transformations get_transformation() const { return transformation; }

  void add_flow(std::shared_ptr<Recording> flow);
  void add_points_video(std::shared_ptr<global::PointsVideo> pv);

  static void scroll_callback(GLFWwindow *window, double xoffset, double yoffset);
  static void cursor_position_callback(GLFWwindow *window, double xpos, double ypos);
  static void mouse_button_callback(GLFWwindow *window, int button, int action, int mods);
  static void reshape_callback(GLFWwindow *window, int w, int h);
  static void close_callback(GLFWwindow *window);
  static void key_callback(GLFWwindow *window, int key, int scancode, int action, int mods);

 protected:
  void rotation_was_changed();
  virtual void update_gl_texture();
  virtual void clear_gl_memory();

  Vec2d mousepos;
  struct {
    bool holding_left  = false;
    bool pressing_left = false;
  } mousebutton;

  float brightness_min                                = std::numeric_limits<float>::lowest();
  float brightness_max                                = std::numeric_limits<float>::max();
  Transformations transformation                      = Transformations::None;
  std::shared_ptr<Transformation::Base> transform_ptr = nullptr;

  ImVec4 clear_color_  = {1.f, 1.f, 1.f, 0.f};
  ColorMap cmap_      = ColorMap::GRAY;
  Vec3f fixed_color_   = {1.f, 0.f, 0.f};
  GLuint texture      = GL_FALSE;
  GLuint ctexture     = GL_FALSE;
  GLuint ctexturediff = GL_FALSE;
  Shader frame_shader;
  GLuint frame_vao, frame_vbo, frame_ebo;
  Shader trace_shader;
  GLuint trace_vao, trace_vbo;
  std::vector<float> trace_vert;
  Shader points_shader;
  GLuint points_vao, points_vbo;
  std::vector<float> points_vert;
};
