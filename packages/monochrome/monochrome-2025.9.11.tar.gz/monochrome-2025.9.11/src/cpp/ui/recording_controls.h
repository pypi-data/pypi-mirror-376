#pragma once

#include "fonts/IconsFontAwesome5.h"
#include "prm.h"
#include "fileformats/SplitFile.h"

void display_recording_metadata(const SharedRecordingPtr &rec) {
  if (!rec->date().empty()) ImGui::TextWrapped("Date: %s", rec->date().c_str());
  if (!rec->comment().empty()) {
    ImGui::TextWrapped("Comment: %s", rec->comment().c_str());
    if (rec->file()->capabilities()[FileCapabilities::SET_COMMENT]) {
      ImGui::SameLine();
      if (ImGui::SmallButton(ICON_FA_EDIT)) {
        rec->comment_edit_ui.comment = rec->comment();
        rec->comment_edit_ui.show    = true;
      }

      if (rec->comment_edit_ui.show) {
        auto window_name = fmt::format("Edit Comment: {}", rec->name());
        ImGui::Begin(window_name.c_str(), nullptr, ImGuiWindowFlags_AlwaysAutoResize);
        ImGui::InputText("##comment", &rec->comment_edit_ui.comment);
        if (ImGui::Button("Save")) {
          rec->file()->set_comment(rec->comment_edit_ui.comment);
          rec->comment_edit_ui.show = false;
        }
        ImGui::SameLine();
        if (ImGui::Button("Cancel")) {
          rec->comment_edit_ui.show    = false;
          rec->comment_edit_ui.comment = rec->comment();
        }
        ImGui::End();
      }
    }
  }
  ImGui::Columns(3);
  ImGui::Text("Frames %d", rec->length());
  ImGui::NextColumn();
  ImGui::Text("Width  %d", rec->Nx());
  ImGui::NextColumn();
  ImGui::Text("Height %d", rec->Ny());
  ImGui::NextColumn();
  if (rec->duration().count() > 0) {
    ImGui::TextWrapped("Duration  %.3fs", rec->duration().count());
    ImGui::NextColumn();
  }
  if (rec->fps() != 0) {
    ImGui::TextWrapped("FPS  %.3f", rec->fps());
    ImGui::NextColumn();
  }
  for (const auto &v : rec->file()->metadata()) {
    ImGui::TextWrapped("%s %s", v.first.c_str(), v.second.c_str());
    ImGui::NextColumn();
  }
  ImGui::Columns(1);
}

void show_export_ui(const SharedRecordingPtr &rec) {
  ImGui::AlignTextToFramePadding();

  auto longest_button_title = ICON_FA_FILE_EXPORT u8" " ICON_FA_VIDEO u8"  Export video file (.mp4, ...)";
  auto button_width = ImGui::CalcTextSize(longest_button_title).x + 4 * ImGui::GetStyle().ItemSpacing.x;
  ImGui::PushStyleVarX(ImGuiStyleVar_ButtonTextAlign, 0.0);
  if (ImGui::Button(ICON_FA_FILE_EXPORT u8" " ICON_FA_FILE_IMAGE u8"   Save screenshot", ImVec2(button_width, 0))) {
    auto &ctrl         = rec->export_ctrl.png;
    ctrl.export_window = true;
    ctrl.assign_auto_filename(rec->file());
  }
  if (ImGui::Button(longest_button_title, ImVec2(button_width, 0))) {
    if (!VideoRecorder::test_ffmpeg() && utils::get_uv_executable() == "uv-placeholder") {
      // No ffmpeg or uv installed. Need to install uv first
      auto builder = subprocess::RunBuilder({utils::get_uv_executable(), "tool", "run", "--from",
                                             "static-ffmpeg", "static_ffmpeg_paths"});
      std::string title = "Downloading ffmpeg...";
      std::string msg =
          "FFmpeg is required to export videos, Monochrome is downloading it now.\n\nPlease click "
          "export video again after the download is complete.";
      global::add_subprocess(builder, title, msg);
    } else {
      auto &ctrl         = rec->export_ctrl.video;
      ctrl.export_window = true;
      ctrl.assign_auto_filename(rec->file());
      ctrl.tend        = rec->length();
      ctrl.description = rec->comment();
    }
  }
  if (rec->length() > 1 && ImGui::Button(ICON_FA_FILE_EXPORT u8" " ICON_FA_IMAGES u8"   Export as image sequence", ImVec2(button_width, 0))) {
    auto &ctrl         = rec->export_ctrl.png;
    ctrl.export_window = true;
    ctrl.assign_auto_filename(rec->file());
  }
  if (!is_rgb_rec(rec) && ImGui::Button(ICON_FA_FILE_EXPORT u8" raw" u8"  Export as raw video", ImVec2(button_width, 0))) {
    auto &ctrl         = rec->export_ctrl.raw;
    ctrl.export_window = true;
    ctrl.start         = {0, 0};
    ctrl.size          = {rec->Nx(), rec->Ny()};
    ctrl.frames        = {0, rec->length()};
    ctrl.assign_auto_filename(rec->file());
  }
  ImGui::PopStyleVar();
}

void show_transformations_ui(const SharedRecordingPtr &rec, RecordingWindow *parent) {
  auto selectable_default_fn = [](bool) {};
  auto selectable            = [rec](const char *label, auto e, auto &&fn) {
    bool is_active = rec->get_transformation() == e;
    if (ImGui::Selectable(label, is_active)) {

      if (is_active) {
        rec->set_transformation(Transformations::None);
        fn(false);
      } else {
        rec->set_transformation(e);
        fn(true);
      }
    }

    return is_active;
  };

  auto kernel_size_select = [rec](unsigned int &val, auto reset_fn) {
    ImGui::Indent(10);
    const int step = 2;
    ImGui::SetNextItemWidth(ImGui::GetContentRegionAvail().x * 0.5f);
    if (ImGui::InputScalar("Kernel size", ImGuiDataType_U32, &val, &step, nullptr, "%d")) {
      reset_fn(rec.get());
    }
    ImGui::Unindent(10);
  };

  if (selectable("Gauss", Transformations::Gauss, selectable_default_fn)) {
    ImGui::Indent(10);
    ImGui::SetNextItemWidth(ImGui::GetContentRegionAvail().x * 0.5f);
    float sigma = Transformation::GaussFilter::get_sigma();
    ImGui::SetNextItemWidth(ImGui::GetContentRegionAvail().x * 1.f);
    if (ImGui::DragFloat("##sigma", &sigma, 0.01, 0, 5, u8"σ = %.2f")) {
      Transformation::GaussFilter::set_sigma(sigma);
    }
    ImGui::Unindent(10);
  }
  if (selectable("Mean", Transformations::Mean, selectable_default_fn)) {
    kernel_size_select(Transformation::MeanFilter::kernel_size,
                        [](RecordingWindow *r) { r->set_transformation(Transformations::Mean); });
  }
  if (selectable("Median", Transformations::Median, selectable_default_fn)) {
    kernel_size_select(Transformation::MedianFilter::kernel_size,
                        [](RecordingWindow *r) { r->set_transformation(Transformations::Median); });
  }
  auto framediff_fn = [rec](bool active) {
    if (active)
      rec->histogram.symmetric = true;
    else
      rec->histogram.symmetric = false;
  };
  if (selectable("Frame Difference", Transformations::FrameDiff, framediff_fn)) {
    ImGui::Indent(10);
    ImGui::SetNextItemWidth(ImGui::GetContentRegionAvail().x * 0.7f);
    ImGui::SliderInt("Frames", &Transformation::FrameDiff::n_frame_diff, 1, 100);
    if (!parent && ImGui::Button("Add As Overlays")) {
      auto new_rec = std::make_shared<RecordingWindow>(rec->file(), Transformations::FrameDiff);
      new_rec->set_name(fmt::format("FrameDiff {}", rec->name()));
      new_rec->colormap(ColorMap::PRGn);
      new_rec->histogram.symmetric = true;
      new_rec->get_min()           = rec->get_min();
      new_rec->get_max()           = rec->get_max();
      new_rec->opacity             = OpacityFunction::CENTERED;
      rec->set_transformation(Transformations::None);
      prm::merge_queue.emplace(new_rec, rec);
    }
    ImGui::Unindent(10);
  }
  if (selectable("Optical Mapping Contrast Enhancement", Transformations::ContrastEnhancement,
                  selectable_default_fn)) {
    ImGui::Indent(10);
    const int step = 2;
    ImGui::SetNextItemWidth(ImGui::GetContentRegionAvail().x * 0.5f);
    if (ImGui::InputScalar("Kernel size", ImGuiDataType_U32,
                            &Transformation::ContrastEnhancement::kernel_size, &step, nullptr,
                            "%d")) {
      rec->set_transformation(Transformations::ContrastEnhancement);
    }
    //      ImGui::SliderInt("Mask", &Transformation::ContrastEnhancement::maskVersion, 0, 2);
    ImGui::Unindent(10);
  }
}

void show_controls_ui(const SharedRecordingPtr &rec, RecordingWindow *parent) {
  ImGui::SeparatorText("General");
  auto rec_name = rec->name();
  if (ImGui::InputText("Name", &rec_name)) {
    rec->set_name(rec_name);
  }
  auto rec_filepath = rec->filepath();
  if (!rec_filepath.empty()) {
    ImGui::InputText("Filepath", &rec_filepath, ImGuiInputTextFlags_ReadOnly);
  }
  auto text_item_size = ImGui::GetItemRectSize();
  if (ImGui::Button(u8"Close " ICON_FA_TRASH_ALT, ImVec2(text_item_size.x, 0))) {
    if (!parent) {
      glfwSetWindowShouldClose(rec->window, GLFW_TRUE);
    } else {
      // Child will be deleted later, after we have left the loop over all children.
      rec->set_context(nullptr);
    }
  }

  {
    if (rec->active) {
      if (ImGui::Button(u8"Hide " ICON_FA_EYE_SLASH, ImVec2(text_item_size.x, 0))) {
        if (!parent) glfwHideWindow(rec->window);
        rec->active = false;
      }
    } else {
      ImGui::EndDisabled();
      if (ImGui::Button(u8"Show " ICON_FA_EYE, ImVec2(text_item_size.x, 0))) {
        rec->active = true;
        if (!parent)
          glfwShowWindow(rec->window);
        else
          rec->playback = parent->playback;
      }
      ImGui::BeginDisabled();
    }
  }

  if (!parent && rec->length() > 1 && rec->length() < 15) {
    if (ImGui::Button("Convert Frames into Image Layers", ImVec2(text_item_size.x, 0))) {
      rec->playback = RecordingPlaybackCtrl(1);
      for (int t = 1; t < rec->length(); t++) {
        auto new_file = std::make_shared<SplitFile>(rec->file(), t);
        auto new_rec  = std::make_shared<RecordingWindow>(new_file);
        prm::merge_queue.emplace(new_rec, rec);
      }
      auto new_file = std::make_shared<SplitFile>(rec->file(), 0);
      rec->file(new_file);
    }
  }

  if (!parent && prm::recordings.size() > 1) {
    if (ImGui::Button(u8"Add as layer onto other recording " ICON_FA_LAYER_GROUP, ImVec2(text_item_size.x, 0)))
      ImGui::OpenPopup("merge_popup");
    if (ImGui::BeginPopup("merge_popup")) {
      for (auto &r : prm::recordings) {
        if (r.get() == rec.get()) continue;
        auto l = fmt::format("Add as layer to '{}'", r->name());
        if (ImGui::Selectable(l.c_str())) {
          prm::merge_queue.emplace(rec, r);
        }
      }
      ImGui::EndPopup();
    }
  }

  ImGui::SeparatorText("Metadata");
  display_recording_metadata(rec);

  if (!is_rgb_rec(rec)) {
    ImGui::SeparatorText("Transformations");
    show_transformations_ui(rec, parent);
  }
}