import logging
import time
from typing import Optional

logger = logging.getLogger("iris.hands.task_executor")


class TaskExecutor:
    """
    Takes a plan from core/ and executes it step by step.
    Reports success/failure back to core/ after each step.
    """

    def __init__(self, app_launcher=None, mouse_keyboard=None, file_ops=None, terminal=None, web_automation=None,
                  code_runner=None, system_monitor=None, window_manager=None, hotkeys=None, system_control=None, understand=None,
                  whatsapp=None, youtube=None, social=None, game_builder=None, website_builder=None):
        self._app_launcher = app_launcher
        self._mouse_keyboard = mouse_keyboard
        self._file_ops = file_ops
        self._terminal = terminal
        self._web = web_automation
        self._code_runner = code_runner
        self._system = system_monitor
        self._windows = window_manager
        self._hotkeys = hotkeys
        self._control = system_control
        self._understand = understand
        self._whatsapp = whatsapp
        self._youtube = youtube
        self._social = social
        self._game_builder = game_builder
        self._website_builder = website_builder
        logger.info("TaskExecutor ready")

    def set_hands(self, app_launcher, mouse_keyboard, file_ops, terminal, web_automation, code_runner=None,
                  system_monitor=None, window_manager=None, hotkeys=None, system_control=None, understand=None,
                  whatsapp=None, youtube=None, social=None, game_builder=None, website_builder=None):
        self._app_launcher = app_launcher
        self._mouse_keyboard = mouse_keyboard
        self._file_ops = file_ops
        self._terminal = terminal
        self._web = web_automation
        self._code_runner = code_runner
        self._system = system_monitor
        self._windows = window_manager
        self._hotkeys = hotkeys
        self._control = system_control
        self._understand = understand
        self._whatsapp = whatsapp
        self._youtube = youtube
        self._social = social
        self._game_builder = game_builder
        self._website_builder = website_builder

    def execute_plan(self, plan: list[dict]) -> dict:
        results = []
        last_created_path = None
        for i, step in enumerate(plan):
            # If step is launch notepad and args is missing or just filename, enrich with full created path
            if step.get("action") == "launch" and step.get("params", {}).get("app", "").lower() == "notepad":
                if last_created_path and (not step.get("params", {}).get("args") or step.get("params", {}).get("args") in last_created_path):
                    step["params"]["args"] = f'"{last_created_path}"'
            elif step.get("action") == "set_working_dir" and last_created_path:
                if not step.get("params", {}).get("path") or step.get("params", {}).get("path") in ("any", "active", "the folder", "folder"):
                    step.setdefault("params", {})["path"] = last_created_path
            elif step.get("action") == "open_in_code_editor" and last_created_path:
                if not step.get("params", {}).get("path") or step.get("params", {}).get("path") in ("any", "active", "the folder", "folder", "project"):
                    step.setdefault("params", {})["path"] = last_created_path

            result = self._execute_step(step)
            results.append({"step": i, "action": step.get("action"), "result": result})

            if isinstance(result, dict) and result.get("success") and result.get("path"):
                last_created_path = result.get("path")

            if not result.get("success"):
                if step.get("critical", False):
                    return {"success": False, "steps_completed": i, "results": results, "failed_at": i, "error": result.get("error", "Step execution failed")}
                results[-1]["result"]["failure_ignored"] = True
        return {"success": all(r.get("result", {}).get("success") for r in results),
                "steps": len(plan), "results": results}

    def _execute_step(self, step: dict) -> dict:
        action = step.get("action", "")
        params = step.get("params", {})

        try:
            if action == "respond":
                return {"success": True, "message": params.get("text", params.get("message", ""))}
            if action == "launch" and self._app_launcher:
                return self._app_launcher.launch(params.get("app", ""), params.get("args", ""))
            elif action == "close_app" and self._app_launcher:
                return self._app_launcher.close(params.get("app", ""), force=params.get("force", False))
            elif action == "click" and self._mouse_keyboard:
                return {"success": self._mouse_keyboard.click(params.get("x", 0), params.get("y", 0))}
            elif action in ("type", "type_text", "type_here"):
                text_val = params.get("text", params.get("words", params.get("message", "")))
                if self._control and hasattr(self._control, "type_text"):
                    return self._control.type_text(text_val)
                elif self._mouse_keyboard:
                    return {"success": self._mouse_keyboard.type_text(text_val), "text": text_val, "message": f"Typed '{text_val}' on here."}
                return {"success": False, "error": "No typing controller available."}
            elif action == "press" and self._mouse_keyboard:
                return {"success": self._mouse_keyboard.press_key(params.get("key", ""))}
            elif action == "screenshot" and self._mouse_keyboard:
                path = self._mouse_keyboard.screenshot(params.get("path"))
                return {"success": bool(path), "path": path}
            elif action in ("create_file", "write_file") and self._file_ops:
                return self._file_ops.create_file(params.get("path", ""), params.get("content", ""))
            elif action == "append_file" and self._file_ops:
                return self._file_ops.append_file(params.get("path", ""), params.get("content", ""))
            elif action == "create_directory" and self._file_ops:
                return self._file_ops.create_directory(params.get("path", ""))
            elif action == "copy" and self._file_ops:
                return self._file_ops.copy(params.get("src", ""), params.get("dst", ""))
            elif action in ("move", "move_file", "move_folder") and self._file_ops:
                return self._file_ops.move(params.get("src", ""), params.get("dst", ""))
            elif action in ("rename", "rename_file", "rename_folder") and self._file_ops:
                return self._file_ops.rename(params.get("path", ""), params.get("new_name", ""))
            elif action in ("delete", "delete_file", "delete_folder") and self._file_ops:
                return self._file_ops.delete(params.get("path", ""), force=params.get("force", True))
            elif action == "search_files" and self._file_ops:
                return self._file_ops.search_files(params.get("directory", "."), params.get("pattern", "*"))
            elif action == "execute_command" and self._terminal:
                return self._terminal.execute(params.get("command", ""), force=params.get("force", False))
            elif action in ("open_cmd_and_run", "run_cmd", "cmd_run") and self._control:
                return self._control.run_cmd(params.get("command", ""), visible=params.get("visible", True))
            elif action == "system_scan" and self._control:
                return self._control.run_system_scan(visible=params.get("visible", True))
            elif action == "open_url" and self._web:
                return self._web.open_url(params.get("url", ""))
            elif action == "fetch_page" and self._web:
                return self._web.fetch_page(params.get("url", ""))
            elif action == "write_and_run" and self._code_runner:
                return self._code_runner.write_and_run(
                    params.get("description", ""),
                    run=params.get("run"),
                    filename=params.get("filename"),
                    target_dir=params.get("target_dir"),
                )
            elif action in ("create_game", "create_and_play_game", "play_game"):
                if not hasattr(self, "_game_builder") or self._game_builder is None:
                    from .game_builder import GameBuilder
                    self._game_builder = GameBuilder(code_runner=self._code_runner, file_ops=self._file_ops)
                return self._game_builder.create_and_play(
                    params.get("game", params.get("target", "offline")),
                    description=params.get("description", ""),
                    target_dir=params.get("target_dir"),
                )
            elif action in ("create_website", "build_website"):
                if not hasattr(self, "_website_builder") or self._website_builder is None:
                    from .website_builder import WebsiteBuilder
                    self._website_builder = WebsiteBuilder(file_ops=self._file_ops)
                return self._website_builder.create_and_open(
                    params.get("topic", params.get("target", "modern")),
                    description=params.get("description", ""),
                    target_dir=params.get("target_dir"),
                )
            elif action == "run_code" and self._code_runner:
                r = self._code_runner.run(params.get("path", ""), timeout=params.get("timeout", 60))
                if isinstance(r, dict) and "path" not in r:
                    r["path"] = params.get("path")
                return r
            elif action == "system_stats" and self._system:
                return self._system.stats()
            elif action == "top_processes" and self._system:
                return self._system.top_processes(limit=params.get("limit", 8))
            elif action == "kill_process" and self._system:
                return self._system.kill_process(params.get("name", ""), pid=params.get("pid"))
            # System Control Actions
            elif action == "set_volume" and self._control:
                return self._control.set_volume(params.get("percent", 50))
            elif action == "volume_up" and self._control:
                return self._control.volume_up(params.get("steps", 5))
            elif action == "volume_down" and self._control:
                return self._control.volume_down(params.get("steps", 5))
            elif action == "mute_volume" and self._control:
                return self._control.mute_volume()
            elif action == "set_brightness" and self._control:
                return self._control.set_brightness(params.get("percent", 50))
            elif action == "brightness_up" and self._control:
                return self._control.brightness_up(params.get("steps", 10))
            elif action == "brightness_down" and self._control:
                return self._control.brightness_down(params.get("steps", 10))
            elif action == "get_brightness" and self._control:
                return self._control.get_brightness()
            elif action == "unlock_pc" and self._control:
                return self._control.unlock_pc(params.get("pin", "224488"))
            elif action == "open_workspace":
                if self._understand:
                    return self._understand.open_workspace(params.get("name", "default"))
                from .understand import UnderstandSystem
                u = UnderstandSystem(app_launcher=self._app_launcher)
                return u.open_workspace(params.get("name", "default"))
            elif action == "wifi_status" and self._control:
                return self._control.get_wifi_status()
            elif action == "connect_wifi" and self._control:
                return self._control.connect_wifi(params.get("ssid", ""))
            elif action == "toggle_wifi" and self._control:
                return self._control.toggle_wifi(params.get("enable", True))
            elif action in ("get_datetime", "date_time", "get_time") and self._control:
                return self._control.get_date_time()
            elif action in ("get_battery", "battery_status") and self._control:
                return self._control.get_battery_status()
            elif action in ("system_power", "power_action") and self._control:
                return self._control.system_power(params.get("action", ""))
            elif action in ("system_updates", "get_updates") and self._control:
                return self._control.get_system_updates()
            elif action in ("media_play_pause", "play", "pause") and self._control:
                if self._youtube and self._youtube._is_playing:
                    return self._youtube.control(action)
                return self._control.media_play_pause()
            elif action in ("media_next", "next_track", "skip") and self._control:
                if self._youtube and self._youtube._is_playing:
                    return self._youtube.control("next")
                return self._control.media_next()
            elif action == "media_prev" and self._control:
                return self._control.media_prev()
            elif action in ("media_rewind", "rewind") and (self._youtube or self._control):
                if self._youtube:
                    return self._youtube.control("rewind")
                return self._control.media_prev()
            elif action in ("media_stop", "stop_music", "stop_song") and self._control:
                if self._youtube and self._youtube._is_playing:
                    return self._youtube.control("stop")
                return self._control.media_stop()
            # Multi-Platform Social Messaging & WhatsApp Actions
            elif action in ("social_open_chat", "social_chat", "whatsapp_open_chat", "whatsapp_chat"):
                platform = params.get("platform", "whatsapp")
                contact = params.get("contact", "")
                if self._social:
                    return self._social.open_chat(platform, contact)
                elif self._whatsapp:
                    return self._whatsapp.open_chat(contact)
                return {"success": False, "error": "No messaging controller available"}
            elif action in ("social_send_message", "social_message", "whatsapp_send_message", "whatsapp_message"):
                platform = params.get("platform", "whatsapp")
                contact = params.get("contact", "")
                message = params.get("message", "")
                if self._social:
                    return self._social.send_message(platform, contact, message)
                elif self._whatsapp:
                    return self._whatsapp.send_message(contact, message)
                return {"success": False, "error": "No messaging controller available"}
            # YouTube Actions
            elif action == "youtube_open" and self._youtube:
                return self._youtube.open_youtube()
            elif action == "youtube_play" and self._youtube:
                return self._youtube.play_song(params.get("song", ""), disambiguate=params.get("disambiguate", False))
            elif action == "youtube_control" and self._youtube:
                return self._youtube.control(params.get("command", "play"))
            elif action == "empty_recycle_bin" and self._control:
                return self._control.empty_recycle_bin()
            elif action == "open_in_code_editor" and self._control:
                return self._control.open_in_code_editor(params.get("path", ""))
            elif action in ("run_in_code_editor", "vscode_run", "execute_in_vscode") and self._control:
                return self._control.run_in_code_editor(params.get("path", params.get("target", "")))
            elif action == "set_working_dir" and self._file_ops:
                target_p = params.get("path", "")
                res = self._file_ops.set_working_dir(target_p)
                active_p = str(self._file_ops.get_working_dir() or target_p)
                return {"success": res, "action": "set_working_dir", "path": active_p, "message": f"Configured '{active_p}' as your active project workspace and opened in VS Code."}
            elif action == "open_folder" and self._control:
                return self._control.open_folder(params.get("folder", "downloads"))
            elif action == "get_clipboard" and self._control:
                return self._control.get_clipboard()
            elif action == "set_clipboard" and self._control:
                return self._control.set_clipboard(params.get("text", ""))
            elif action == "list_windows" and self._windows:
                return self._windows.list_windows(limit=params.get("limit", 20))
            elif action in ("focus_window", "focus", "bring_to_front") and self._windows:
                target_title = params.get("title") or params.get("target") or params.get("app") or params.get("window") or ""
                return self._windows.focus(target_title)
            elif action in ("minimize_window", "minimize") and self._windows:
                target_title = params.get("title") or params.get("target") or params.get("app") or params.get("window") or ""
                if not target_title or target_title.lower().strip() in ("all", "things", "the things", "everything", "screen", "tabs", "the tabs", "windows", "the windows", "it", "this"):
                    return self._windows.show_desktop()
                return self._windows.minimize(target_title)
            elif action in ("maximize_window", "maximize") and self._windows:
                target_title = params.get("title") or params.get("target") or params.get("app") or params.get("window") or ""
                return self._windows.maximize(target_title)
            elif action in ("restore_window", "restore") and self._windows:
                target_title = params.get("title") or params.get("target") or params.get("app") or params.get("window") or ""
                return self._windows.focus(target_title)
            elif action in ("snap_window", "snap") and self._windows:
                target_title = params.get("title") or params.get("target") or params.get("app") or params.get("window") or ""
                side = params.get("side", "left")
                return self._windows.snap(target_title, side=side)
            elif action in ("show_desktop", "minimize_all", "go_to_desktop", "minimize_tabs", "minimize_all_tabs", "minimize_things", "minimize_the_things", "minimize_everything") and self._windows:
                return self._windows.show_desktop()
            elif action in ("close_window", "close") and self._windows:
                target_title = params.get("title") or params.get("target") or params.get("app") or params.get("window") or ""
                return self._windows.close(target_title)
            elif action == "navigate" and self._web:
                return self._web.navigate(params.get("url", ""))
            elif action == "fill_form" and self._web:
                return self._web.fill_form(params.get("url", ""), params.get("fields", {}),
                                           submit=params.get("submit", False))
            elif action == "web_click" and self._web:
                return self._web.click(params.get("selector", ""))
            elif action == "extract_text" and self._web:
                return self._web.extract_text(params.get("selector", "body"))
            elif action == "wait":
                time.sleep(params.get("seconds", 1))
                return {"success": True}
            else:
                return {"success": False, "error": f"Unknown action or missing handler: {action}"}
        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict:
        return {
            "app_launcher_available": self._app_launcher is not None,
            "mouse_keyboard_available": self._mouse_keyboard is not None,
            "file_ops_available": self._file_ops is not None,
            "terminal_available": self._terminal is not None,
            "web_automation_available": self._web is not None,
            "code_runner_available": self._code_runner is not None,
            "system_monitor_available": self._system is not None,
            "window_manager_available": self._windows is not None,
            "hotkeys_available": self._hotkeys is not None,
            "system_control_available": self._control is not None,
        }
