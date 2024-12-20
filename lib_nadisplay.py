
from typing import Callable, Any, Optional, Type, cast

import time

from threading import Thread, Lock, Condition

import atexit

import os
import math
import random
import pickle

import numpy as np

import lib_nadisplay_events as nd_event
from lib_nadisplay_colors import ND_Color, cl, ND_Transformations
from lib_nadisplay_rects import ND_Rect, ND_Point, ND_Position, ND_Position_Constraints, ND_Position_Margins



#
def clamp(value: Any, mini: Any, maxi: Any) -> Any:
    if value < mini:
        return mini
    elif value > maxi:
        return maxi
    return value


#
def get_percentage_from_str(t: str) -> float:
    #
    t = t.strip()
    #
    if not t.endswith("%"):
        return 0
    #
    try:
        v: float = float(t[:-1])
        return v
    except Exception as _:
        return 0


#
def get_font_size(txt: str, font_size: int, font_ratio: float = 3.0 / 4.0) -> tuple[int, int]:
    return (len(txt) * int(float(font_size) * font_ratio), font_size)


#
class ND_MainApp:
    #
    def __init__(self, DisplayClass: Type["ND_Display"], WindowClass: Type["ND_Window"], EventsManagerClass: Type["ND_EventsManager"], global_vars_to_save: list[str] = [], path_to_global_vars_save_file: str = "") -> None:
        #
        self.global_vars: dict[str, Any] = {}
        self.global_vars_muts: dict[str, Lock] = {}
        self.global_vars_creation_mut: Lock = Lock()
        #
        self.global_vars_to_save: list[str] = global_vars_to_save
        self.path_to_global_vars_save_file: str = path_to_global_vars_save_file
        #
        self.fps_display: int = 60
        self.fps_physics: int = 60
        self.fps_other_fns: int = 60
        self.frame_duration_display: float = 1000.0 / float(self.fps_display)
        self.frame_duration_physics: float = 1000.0 / float(self.fps_physics)
        self.frame_duration_other_fns: float = 1000.0 / float(self.fps_other_fns)
        #
        self.current_fps: int = 0
        #
        self.is_running: bool = False
        self.is_threading: bool = True
        #
        self.display: Optional["ND_Display"] = DisplayClass(self, WindowClass=WindowClass)
        #
        if self.display is not None:
            self.display.init_display()
        #
        self.events_manager: "ND_EventsManager" = EventsManagerClass(self)
        #
        self.init_queue_functions: list[Callable[[ND_MainApp], None]] = []
        #
        self.mainloop_queue_functions: dict[str, list[Callable[[ND_MainApp, float], None]]] = {
            "physics": []
        }
        self.mainloop_queue_fns_mutex: Lock = Lock()
        #
        self.events_functions: dict[str, list[Callable[[ND_MainApp], None]]] = {}
        self.events_functions_mutex: Lock = Lock()
        #
        self.threads: list[Thread] = []
        self.threads_names: list[str] = []
        self.threads_ids_not_joined: set[int] = set()
        self.mutex_threads_creation: Lock = Lock()
        self.threads_condition: Condition = Condition()
        #
        #
        if self.path_to_global_vars_save_file != "" and os.path.exists(self.path_to_global_vars_save_file):
            #
            self.global_vars_load_from_path(self.path_to_global_vars_save_file)

    #
    def atexit(self) -> None:
        #
        print("At exit catched")
        #
        if self.global_vars_to_save and self.path_to_global_vars_save_file != "":
            self.global_vars_save_to_path(path=self.path_to_global_vars_save_file, vars_to_save=self.global_vars_to_save)
        #
        self.is_running = False
        #
        if self.is_threading:
            self.waiting_all_threads()

    #
    def get_time_msec(self) -> float:
        #
        if self.display is not None:
            return self.display.get_time_msec()
        #
        else:
            return time.time() * 1000.0

    #
    def wait_time_msec(self, delay_in_msec: float) -> None:
        #
        if self.display is not None:
            self.display.wait_time_msec(delay_in_msec)
        #
        time.sleep(delay_in_msec / 1000.0)

    #
    def global_vars_save_to_path(self, path: str, vars_to_save: list[str]) -> None:
        #
        data_to_save: dict[str, Any] = {}
        #
        for var in vars_to_save:
            if var in self.global_vars:
                #
                # print(f"DEBUG | global vars save {var}={self.global_vars[var]}")
                #
                data_to_save[var] = self.global_vars[var]
        #
        with open(path, "wb") as f:
            pickle.dump(data_to_save, f)
        #
        print(f"MainApp : saved global vars to {path}")
        #

    #
    def global_vars_load_from_path(self, path: str) -> None:
        #
        with open(path, "rb") as f:
            data_to_load: dict[str, Any] = pickle.load(f)
        #
        for key in data_to_load:
            #
            # print(f"DEBUG | global vars load {key}={data_to_load[key]}")
            #
            self.global_vars_set(key, data_to_load[key])
        #
        print(f"MainApp : loaded global vars from {path}")
        #

    #
    def global_vars_create(self, var_name: str, var_value: Any, if_exists: str = "ignore") -> None:
        #
        self.global_vars_creation_mut.acquire()
        #
        if var_name not in self.global_vars:
            #
            self.global_vars[var_name] = var_value
            self.global_vars_muts[var_name] = Lock()
            #
        else:
            #
            if if_exists == "override":
                self.global_vars[var_name] = var_value
            #
        #
        self.global_vars_creation_mut.release()

    #
    def global_vars_get_optional(self, var_name: str) -> Optional[Any]:
        #
        if var_name in self.global_vars:
            return self.global_vars[var_name]
        return None

    # If is in global vars, returns it, else return default_value, all the cases, that is not None
    def global_vars_get_default(self, var_name: str, default_value: Any) -> Any:
        #
        if var_name in self.global_vars:
            return self.global_vars[var_name]
        #
        return default_value

    # Get Not None
    def global_vars_get(self, var_name: str) -> Any:
        #
        if var_name in self.global_vars:
            return self.global_vars[var_name]
        #
        raise IndexError(f"CRITICAL ERROR !\nGlobal Vars Error: Index {var_name} not found in global variables !")

    #
    def global_vars_set(self, var_name: str, var_value: Any, if_not_exists: str = "create") -> None:
        #
        if var_name in self.global_vars:
            #
            with self.global_vars_muts[var_name]:
                #
                self.global_vars[var_name] = var_value
            #
        else:
            #
            if if_not_exists == "create":
                #
                with self.global_vars_creation_mut:
                    #
                    self.global_vars[var_name] = var_value
                    self.global_vars_muts[var_name] = Lock()

    #
    def global_vars_list_append(self, var_name: str, obj_value: Any, if_not_exists: str = "create") -> None:
        #
        if var_name in self.global_vars:
            #
            with self.global_vars_muts[var_name]:
                #
                self.global_vars[var_name].append(obj_value)
            #
        else:
            #
            if if_not_exists == "create":
                #
                with self.global_vars_creation_mut:
                    #
                    self.global_vars[var_name] = [obj_value]
                    self.global_vars_muts[var_name] = Lock()

    #
    def global_vars_list_remove(self, var_name: str, obj_value: Any, if_not_exists: str = "ignore") -> None:
        #
        if var_name in self.global_vars:
            #
            with self.global_vars_muts[var_name]:
                #
                self.global_vars[var_name].remove(obj_value)
            #
        else:
            #
            if not if_not_exists == "error":
                raise UserWarning("#TODO: complete error message")

    #
    def global_vars_list_del_at_idx(self, var_name: str, idx: int, if_not_exists: str = "ignore") -> None:
        #
        if var_name in self.global_vars:
            #
            with self.global_vars_muts[var_name]:
                #
                del self.global_vars[var_name][idx]
            #
        else:
            #
            if not if_not_exists == "error":
                raise UserWarning("#TODO: complete error message")

    #
    def global_vars_list_length(self, var_name: str) -> int:
        #
        if var_name in self.global_vars:
            #
            return len(self.global_vars[var_name])
            #
        else:
            #
            return 0

    #
    def global_vars_list_get_at_idx(self, var_name: str, idx: int) -> Optional[Any]:
        #
        if var_name in self.global_vars:
            #
            if idx < len(self.global_vars[var_name]):
                return self.global_vars[var_name][idx]
            #
            else:
                return None
            #
        else:
            #
            return None

    #
    def global_vars_list_set_at_idx(self, var_name: str, idx: int, obj_value: Any, if_not_exists: str = "error", if_idx_not_in_list_length: str = "error") -> None:
        #
        if var_name in self.global_vars:
            #
            with self.global_vars_muts[var_name]:
                #
                if idx < len(self.global_vars[var_name]):
                    self.global_vars[var_name][idx] = obj_value
                else:
                    #
                    if if_idx_not_in_list_length == "error":
                        #
                        raise UserWarning("Error, #TODO: complete error message")
            #
        else:
            #
            if if_not_exists == "error":
                #
                raise UserWarning("Error, #TODO: complete error message")

    #
    def global_vars_dict_set(self, var_name: str, dict_key: Any, obj_value: Any, if_not_exists: str = "ignore") -> None:
        #
        if var_name in self.global_vars:
            #
            with self.global_vars_muts[var_name]:
                #
                self.global_vars[var_name][dict_key] = obj_value
            #
        else:
            #
            if if_not_exists == "create":
                #
                with self.global_vars_creation_mut:
                    #
                    self.global_vars[var_name] = {
                        dict_key: obj_value
                    }
                    self.global_vars_muts[var_name] = Lock()

    #
    def global_vars_dict_get(self, var_name: str, dict_key: Any, if_not_exists: str = "none") -> Any:
        #
        if var_name in self.global_vars:
            #
            return self.global_vars[var_name][dict_key]
            #
        else:
            #
            if if_not_exists == "error":
                #
                raise UserWarning("Error, #TODO: complete error message")
            #
            elif if_not_exists == "none":
                #
                return None

    #
    def global_vars_dict_del(self, var_name: str, dict_key: Any, if_not_exists: str = "ignore") -> None:
        #
        if var_name in self.global_vars:
            #
            with self.global_vars_muts[var_name]:
                #
                del self.global_vars[var_name][dict_key]
            #
        else:
            #
            if not if_not_exists == "error":
                raise UserWarning("#TODO: complete error message")

    #
    def global_vars_exists(self, var_name: str) -> bool:
        return var_name in self.global_vars

    #
    def get_element(self, window_id: int, scene_id: str, elt_id: str) -> Optional["ND_Elt"]:
        #
        if not self.display:
            return None
        #
        if window_id not in self.display.windows:
            return None
        #
        win: Optional[ND_Window] = self.display.windows[window_id]
        #
        if not win:
            return None
        #
        if scene_id not in win.scenes:
            return None
        #
        if elt_id in win.scenes[scene_id].elements_by_id:
            return win.scenes[scene_id].elements_by_id[elt_id]
        #
        for elt in win.scenes[scene_id].elements_by_id.values():
            if isinstance(elt, ND_Container):
                r: Optional[ND_Elt] = self.get_element_recursively_from_container(elt, elt_id)
                if r is not None:
                    return r
            if isinstance(elt, ND_MultiLayer):
                r = self.get_element_recursively_from_multilayer(elt, elt_id)
                if r is not None:
                    return r
        #
        return None

    #
    def get_element_value(self, window_id: int, scene_id: str, elt_id: str) -> Optional[bool | int | float | str]:
        #
        elt: Optional[ND_Elt] = self.get_element(window_id, scene_id, elt_id)
        #
        if elt is None:
            return None
        #
        if isinstance(elt, ND_LineEdit):
            return elt.text
        elif isinstance(elt, ND_Checkbox):
            return elt.checked
        elif isinstance(elt, ND_NumberInput):
            return elt.value
        elif isinstance(elt, ND_SelectOptions):
            return elt.value
        #
        return None

    #
    def get_element_recursively_from_multilayer(self, elt_cont: "ND_MultiLayer", elt_id: str) -> Optional["ND_Elt"]:
        #
        if elt_id in elt_cont.elements_by_id:
            return elt_cont.elements_by_id[elt_id]
        #
        for elt in elt_cont.elements_by_id.values():
            if isinstance(elt, ND_Container):
                r: Optional[ND_Elt] = self.get_element_recursively_from_container(elt, elt_id)
                if r is not None:
                    return r
            if isinstance(elt, ND_MultiLayer):
                r = self.get_element_recursively_from_multilayer(elt, elt_id)
                if r is not None:
                    return r
        #
        return None

    #
    def get_element_recursively_from_container(self, elt_cont: "ND_Container", elt_id: str) -> Optional["ND_Elt"]:
        #
        if elt_id in elt_cont.elements_by_id:
            return elt_cont.elements_by_id[elt_id]
        #
        for elt in elt_cont.elements_by_id.values():
            if isinstance(elt, ND_Container):
                r: Optional[ND_Elt] = self.get_element_recursively_from_container(elt, elt_id)
                if r is not None:
                    return r
            if isinstance(elt, ND_MultiLayer):
                r = self.get_element_recursively_from_multilayer(elt, elt_id)
                if r is not None:
                    return r
        #
        return None

    #
    def add_function_to_mainloop_fns_queue(self, mainloop_name: str, function: Callable) -> None:
        #
        with self.mainloop_queue_fns_mutex:
            #
            if mainloop_name not in self.mainloop_queue_functions:
                self.mainloop_queue_functions[mainloop_name] = []
            #
            self.mainloop_queue_functions[mainloop_name].append(function)

    #
    def add_functions_to_mainloop_fns_queue(self, mainloop_name: str, functions: list[Callable]) -> None:
        #
        with self.mainloop_queue_fns_mutex:
            #
            if mainloop_name not in self.mainloop_queue_functions:
                self.mainloop_queue_functions[mainloop_name] = []
            #
            self.mainloop_queue_functions[mainloop_name] += functions

    #
    def delete_mainloop_fns_queue(self, mainloop_name: str) -> None:
        #
        with self.mainloop_queue_fns_mutex:
            #
            if mainloop_name in self.mainloop_queue_functions:
                self.mainloop_queue_functions[mainloop_name] = []
                del self.mainloop_queue_functions[mainloop_name]

    #
    def get_mainloop_fns_queue(self, mainloop_name: str) -> list[Callable]:
        #
        if mainloop_name not in self.mainloop_queue_functions:
            return []
        #
        return self.mainloop_queue_functions[mainloop_name]

    #
    def add_function_to_event_fns_queue(self, event_name: str, fn: Callable[..., None]) -> None:
        #
        with self.events_functions_mutex:
            #
            if event_name not in self.events_functions:
                #
                self.events_functions[event_name] = []
            #
            self.events_functions[event_name].append( fn )
        #

    #
    def display_thread(self) -> None:

        start_time: float = 0.0
        elapsed_time: float = 0.0
        delay: float = 0.0  # Delay with first frame

        #
        while self.is_running:
            #
            elapsed_time = self.get_time_msec()
            if start_time != 0:
                delay = elapsed_time - start_time
                if delay != 0:
                    self.current_fps = int(1.0 / delay)
            #
            start_time = elapsed_time    # Start of the frame in milliseconds

            #
            if self.display is not None:
                #
                self.display.update_display()

            # Calculate the time taken for this frame
            elapsed_time = self.get_time_msec() - start_time

            # If the frame was rendered faster than the target duration, delay
            if elapsed_time < self.frame_duration_display:
                self.wait_time_msec(self.frame_duration_display - elapsed_time)

    #
    def handle_event_to_display_windows(self, event: nd_event.ND_Event) -> None:
        #
        if self.display is None:
            return
        #
        win: Optional[ND_Window]
        for win in list(self.display.windows.values()):
            #
            if win is None or not win.is_hovered_by_mouse():
                continue
            #
            scene: ND_Scene
            for scene in win.scenes.values():
                scene.handle_event(event)  # Potentiel Blockage ici lors de la fermeture de l'application

    #
    def handle_windows_event(self, event: nd_event.ND_EventWindow) -> str:
        #
        if self.display is None:
            return ""

        #
        window: Optional[ND_Window] = self.display.get_window(event.window_id)

        #
        if window is None:
            return ""

        #
        if isinstance(event, nd_event.ND_EventWindowClose):
            #
            self.display.destroy_window(window.window_id)
            #
            return "window_close"
        #
        elif isinstance(event, nd_event.ND_EventWindowMoved):
            #
            window.update_position(event.x, event.y)
            #
            return "window_moved"
        #
        elif isinstance(event, nd_event.ND_EventWindowResized):
            #
            window.update_size(event.w, event.h)
            #
            scene: ND_Scene
            for scene in window.scenes.values():
                #
                scene.handle_window_resize()
            #
            return "window_resized"

        #
        return ""

    #
    def manage_events(self) -> bool:
        #
        event: Optional[nd_event.ND_Event] = self.events_manager.poll_next_event()

        #
        if event is None:
            return False

        #
        event_name: str = ""

        #
        if isinstance(event, nd_event.ND_EventQuit):
            #
            self.quit()
            #
            return True

        #
        elif isinstance(event, nd_event.ND_EventKeyDown) and event.key != "":
            event_name = f"keydown_{event.key}"

        #
        elif isinstance(event, nd_event.ND_EventKeyUp) and event.key != "":
            event_name = f"keyup_{event.key}"

        #
        elif isinstance(event, nd_event.ND_EventWindow):
            #
            if isinstance(event, nd_event.ND_EventWindowShown) or isinstance(event, nd_event.ND_EventWindowHidden):
                return True
            #
            event_name = self.handle_windows_event(event)

        #
        self.handle_event_to_display_windows(event)

        #
        if False and event_name != "":
            print(f"EVENT NAME : {event_name}")

        #
        if event_name in self.events_functions:
            #
            for fn in self.events_functions[event_name]:
                fn(self)
        #
        return True

    #
    def events_thread(self) -> None:
        #
        while self.is_running:
            #
            self.manage_events()

    #
    def start_events_thread(self) -> None:
        #
        if not self.is_threading:
            return
        #
        if self.display is not None and not self.display.events_thread_in_main_thread:
            return
        #
        self.create_thread( self.events_thread, thread_name = "events_threads")
        print(f" - thread {self.threads[-1]} for events created")

    #
    def custom_function_queue_thread(self, thread_name: str) -> None:
        #
        start_time: float = 0.0
        elapsed_time: float = 0.0

        #
        while self.is_running:
            #
            start_time = self.get_time_msec()  # Start of the frame in milliseconds
            #
            for fn in self.mainloop_queue_functions[thread_name]:
                fn(self, elapsed_time)
            #

            # Calculate the time taken for this frame
            elapsed_time = self.get_time_msec() - start_time

            # If the frame was rendered faster than the target duration, delay
            if thread_name == "physics":
                if elapsed_time < self.frame_duration_physics:
                    self.wait_time_msec(self.frame_duration_physics - elapsed_time)
            else:
                if elapsed_time < self.frame_duration_other_fns:
                    self.wait_time_msec(self.frame_duration_other_fns - elapsed_time)

    #
    def start_init_queue_functions(self) -> None:
        #
        print("\nBegin to exec all init functions in order\n")

        # Init functions queue
        for fn in self.init_queue_functions:
            fn(self)
            print(f" - Init function called {fn}")

        print("\nAll Init functions called\n")

    #
    def create_all_threads(self) -> None:
        #
        if not self.is_threading:
            return
        #
        print("\nBegin to start threads\n")

        # Display thread
        if self.display is not None and not self.display.display_thread_in_main_thread:
            self.create_thread( self.display_thread, thread_name="display_thread")
            print(f" - thread {self.threads[-1]} for display created")

        # All the other functions thread
        thread_name: str
        for thread_name in self.mainloop_queue_functions:
            self.create_thread( self.custom_function_queue_thread, [thread_name], thread_name=thread_name )

        # Start threads
        for thread in self.threads:
            thread.start()
            print(f" - custom thread {thread} created")

        print("\nAll thread created\n")

    #
    def thread_wrap_fn(self, fn_to_call: Callable, fn_to_call_args: list[Any]) -> None:

        #
        fn_to_call(*fn_to_call_args)

        #
        with self.threads_condition:
            self.threads_condition.notify_all()

    #
    def create_thread(self, fn_to_call: Callable, fn_to_call_args: list[Any] = [], thread_name: str = "unknown thread") -> int:
        #
        if not self.is_threading:
            return -1
        #
        id_thread: int = -1

        #
        with self.mutex_threads_creation:
            #
            id_thread = len(self.threads)
            self.threads_ids_not_joined.add( id_thread )

            #
            self.threads.append(
                Thread( target=self.thread_wrap_fn, args=[fn_to_call, fn_to_call_args] )
            )
            self.threads_names.append( thread_name )

        #
        return id_thread

    #
    def waiting_all_threads(self) -> None:
        #
        if not self.is_threading:
            return
        #
        print("\nWaiting for threads to finish...\n")

        # While not all threads are done
        while self.threads_ids_not_joined:
            #
            spc: str = "\n - "
            print(f"Threads to wait :\n  - {spc.join([str(self.threads_names[t]) for t in list(self.threads_ids_not_joined)])}")
            #
            with self.threads_condition:
                #
                self.threads_condition.wait()  # Will block here until notified
                #
                for thread_id in list(self.threads_ids_not_joined):
                    #
                    if not self.threads[thread_id].is_alive():  # Check if the thread has finished
                        #
                        print(f"  -> Waiting for thread {thread_id} ({self.threads[thread_id]}) to join...")
                        #
                        self.threads[thread_id].join()          # Join the thread if it's done
                        print(f" - thread {self.threads[thread_id]} joined")
                        self.threads_ids_not_joined.remove(thread_id)  # Remove it from the list
                    #
                    print("    * done.")

        #
        print("\nAll threads joined\n")

    #
    def mainloop_without_threads(self) -> None:
        #
        start_time: float = 0.0
        elapsed_time: float = 0.0
        delay: float = 0.0  # Delay with first frame

        #
        while self.is_running:
            #
            elapsed_time = self.get_time_msec()
            if start_time != 0:
                delay = elapsed_time - start_time
                if delay != 0:
                    self.current_fps = int(1.0 / delay)
            #
            start_time = elapsed_time    # Start of the frame in milliseconds

            # Manage events
            max_events_per_frame: int = 200
            current_events_per_frame: int = 0
            while self.manage_events() and current_events_per_frame < max_events_per_frame:
                current_events_per_frame += 1

            # Manage all the other mainloop runs
            queue_name: str
            fn: Callable[[ND_MainApp, float], None]
            for queue_name in self.mainloop_queue_functions:
                for fn in self.mainloop_queue_functions[queue_name]:
                    fn(self, elapsed_time)

            #
            if self.display is not None:
                #
                self.display.update_display()

            # Calculate the time taken for this frame
            elapsed_time = self.get_time_msec() - start_time

            # If the frame was rendered faster than the target duration, delay
            if elapsed_time < self.frame_duration_display:
                self.wait_time_msec(self.frame_duration_display - elapsed_time)

    #
    def mainloop_threads_display_and_events(self) -> None:
        #
        start_time: float = 0.0
        elapsed_time: float = 0.0
        delay: float = 0.0  # Delay with first frame

        #
        while self.is_running:
            #
            elapsed_time = self.get_time_msec()
            if start_time != 0:
                delay = elapsed_time - start_time
                if delay != 0:
                    self.current_fps = int(1.0 / delay)
                print(f"Fps : {self.current_fps}")
            #
            start_time = elapsed_time    # Start of the frame in milliseconds

            # Manage events
            max_events_per_frame: int = 200
            current_events_per_frame: int = 0
            while self.manage_events() and current_events_per_frame < max_events_per_frame:
                current_events_per_frame += 1

            #
            if self.display is not None:
                #
                self.display.update_display()

            # Calculate the time taken for this frame
            elapsed_time = self.get_time_msec() - start_time

            # If the frame was rendered faster than the target duration, delay
            if elapsed_time < self.frame_duration_display:
                self.wait_time_msec(self.frame_duration_display - elapsed_time)

    #
    def run(self) -> None:
        #
        atexit.register(self.atexit)
        #
        self.is_running = True
        #
        print("\nBeginning of the app...\n")
        #
        self.start_init_queue_functions()
        #
        if self.display is not None and not self.display.main_not_threading:
            self.is_threading = False
        self.is_threading = False
        #
        if self.is_threading:
            self.create_all_threads()
        #
        if self.display is not None:
            if not self.display.main_not_threading:
                if self.display.display_thread_in_main_thread and not self.display.events_thread_in_main_thread:
                    self.display_thread()
                elif not self.display.display_thread_in_main_thread and self.display.events_thread_in_main_thread:
                    self.events_thread()
                elif not self.display.display_thread_in_main_thread and self.display.events_thread_in_main_thread:
                    self.mainloop_threads_display_and_events()
            else:
                self.mainloop_without_threads()
        #
        if self.is_threading:
            self.waiting_all_threads()

    #
    def quit(self) -> None:
        #
        self.is_running = False
        #
        if self.display is not None:
            self.display.destroy_display()
        #
        exit(0)


#
class ND_Display:
    #
    def __init__(self, main_app: ND_MainApp, WindowClass: Type["ND_Window"]) -> None:
        #
        self.main_not_threading: bool = False
        self.events_thread_in_main_thread: bool = False
        self.display_thread_in_main_thread: bool = False
        #
        self.main_app: ND_MainApp = main_app
        #
        self.font_names: dict[str, str] = {}
        self.ttf_fonts: dict[str, dict[int, object]] = {}
        self.default_font: str = "FreeSans"
        #
        self.windows: dict[int, Optional[ND_Window]] = {}
        self.thread_create_window: Lock = Lock()
        #
        self.vulkan_instance: Optional[object] = None
        #
        self.shader_program: int = -1
        self.shader_program_textures: int = -1
        #
        self.mutex_display: Lock = Lock()

    #
    def get_time_msec(self) -> float:
            return time.time() * 1000.0

    #
    def wait_time_msec(self, delay_in_msec: float) -> None:
        time.sleep(delay_in_msec / 1000.0)

    #
    def load_system_fonts(self) -> None:
        """Scans system directories for fonts and adds them to the font_names dictionary."""
        return

    #
    def init_display(self) -> None:
        #
        return

    #
    def destroy_display(self) -> None:
        #
        return

    #
    def add_font(self, font_path: str, font_name: str) -> None:
        #
        return

    #
    def get_font(self, font: str, font_size: int) -> Optional[object]:
        #
        return None

    #
    def update_display(self) -> None:
        #
        return

    #
    def get_focused_window_id(self) -> int:
        return -1

    #
    def create_window(self, window_params: dict[str, Any], error_if_win_id_not_available: bool = False) -> int:
        #
       return -1

    #
    def get_window(self, window_id: int) -> Optional["ND_Window"]:
        #
        if window_id not in self.windows:
            #
            return None
        #
        return self.windows[window_id]

    #
    def destroy_window(self, win_id: int) -> None:
        #
        return


#
class ND_Window:
    #
    def __init__(
            self,
            display: ND_Display,
            window_id: int,
            init_state: Optional[str] = None
        ):

        #
        self.window_id: int = window_id

        #
        self.display: ND_Display = display

        #
        self.main_app: ND_MainApp = self.display.main_app

        # Global Window Position in Global Desktop Space
        self.x: int = 0
        self.y: int = 0
        self.width: int = 640
        self.height: int = 480

        # Warning: This has to be updated at each change !
        self.rect: ND_Rect = ND_Rect(self.x, self.y, self.width, self.height)

        #
        self.sdl_or_glfw_window_id: int = -1

        #
        self.display_states: dict[str, Optional[Callable[[], None]]] = {}
        #
        self.state: Optional[str] = init_state

        #
        self.scenes: dict[str, ND_Scene] = {}

        #
        self.next_texture_id: int = 0

    #
    def destroy_window(self) -> None:
        #
        return

    #
    def set_title(self, new_title: str) -> None:
        #
        return

    #
    def set_position(self, new_x: int, new_y: int) -> None:
        #
        return

    #
    def update_position(self, new_x: int, new_y: int) -> None:
        #
        self.x, self.y = new_x, new_y
        #
        self.rect = ND_Rect(self.x, self.y, self.width, self.height)

    #
    def update_size(self, new_w: int, new_h: int) -> None:
        #
        self.width, self.height = new_w, new_h
        #
        self.rect = ND_Rect(self.x, self.y, self.width, self.height)

    #
    def set_fullscreen(self, mode: int) -> None:
        #
        return

    #
    def set_size(self, new_width: int, new_height: int) -> None:
        #
        return

    #
    def add_scene(self, scene: "ND_Scene") -> None:
        #
        self.scenes[scene.scene_id] = scene

    #
    def update_scene_sizes(self) -> None:
        #
        scene: ND_Scene
        for scene in self.scenes.values():
            #
            scene.handle_window_resize()

    #
    def set_state(self, state: str) -> None:
        #
        self.state = state

    #
    def is_hovered_by_mouse(self) -> bool:
        #
        rect_window: ND_Rect = ND_Rect(self.x, self.y, self.width, self.height)
        pt_mouse: ND_Point = self.display.main_app.events_manager.get_global_mouse_position()
        #
        return rect_window.contains_point( pt_mouse )

    #
    def blit_texture(self, texture, dst_rect) -> None:
        #
        return

    #
    def prepare_text_to_render(self, text: str, color: ND_Color, font_size: int, font_name: Optional[str] = None) -> int:
        #
        return -1

    #
    def prepare_image_to_render(self, img_path: str) -> int:
        #
        return -1

    #
    def render_prepared_texture(self, texture_id: int, x: int, y: int, width: int, height, transformations: ND_Transformations = ND_Transformations()) -> None:
        #
        return

    #
    def render_part_of_prepared_texture(self, texture_id: int, x: int, y: int, w: int, h: int, src_x: int, src_y: int, src_w: int, src_h: int, transformations: ND_Transformations = ND_Transformations()) -> None:
        #
        return

    #
    def get_prepared_texture_size(self, texture_id: int) -> ND_Point:
        #
        return ND_Point(0, 0)

    #
    def destroy_prepared_texture(self, texture_id: int) -> None:
        #
        return

    #
    def draw_text(self, txt: str, x: int, y: int, font_size: int, font_color: ND_Color, font_name: Optional[str] = None) -> None:
        #
        return

    #
    def get_text_size_with_font(self, txt: str, font_size: int, font_name: Optional[str] = None) -> ND_Point:
        #
        return ND_Point(0, 0)

    #
    def get_count_of_renderable_chars_fitting_given_width(self, txt: str, given_width: int, font_size: int, font_name: Optional[str] = None) -> tuple[int, int]:
        #
        return 0, 0

    #
    def draw_pixel(self, x: int, y: int, color: ND_Color) -> None:
        #
        return

    #
    def draw_hline(self, x1: int, x2: int, y: int, color: ND_Color) -> None:
        #
        return

    #
    def draw_vline(self, x: int, y1: int, y2: int, color: ND_Color) -> None:
        #
        return

    #
    def draw_line(self, x1: int, x2: int, y1: int, y2: int, color: ND_Color) -> None:
        #
        return

    #
    def draw_thick_line(self, x1: int, x2: int, y1: int, y2: int, line_thickness: int, color: ND_Color) -> None:
        #
        return

    #
    def draw_rounded_rect(self, x: int, y: int, width: int, height: int, radius: int, fill_color: ND_Color, border_color: ND_Color) -> None:
        #
        return

    #
    def draw_unfilled_rect(self, x: int, y: int, width: int, height: int, outline_color: ND_Color) -> None:
        #
        return

    #
    def draw_filled_rect(self, x: int, y: int, width: int, height: int, outline_color: ND_Color) -> None:
        #
        return

    #
    def draw_unfilled_circle(self, x: int, y: int, radius: int, outline_color: ND_Color) -> None:
        #
        return

    #
    def draw_filled_circle(self, x: int, y: int, radius: int, fill_color: ND_Color) -> None:
        #
        return

    #
    def draw_unfilled_ellipse(self, x: int, y: int, rx: int, ry: int, outline_color: ND_Color) -> None:
        #
        return

    #
    def draw_filled_ellipse(self, x: int, y: int, rx: int, ry: int, fill_color: ND_Color) -> None:
        #
        return

    #
    def draw_arc(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, color: ND_Color) -> None:
        #
        return

    #
    def draw_unfilled_pie(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, outline_color: ND_Color) -> None:
        #
        return

    #
    def draw_filled_pie(self, x: int, y: int, radius: float, angle_start: float, angle_end: float, fill_color: ND_Color) -> None:
        #
        return

    #
    def draw_unfilled_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, outline_color: ND_Color) -> None:
        #
        return

    #
    def draw_filled_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, filled_color: ND_Color) -> None:
        #
        return

    #
    def draw_unfilled_polygon(self, x_coords: list[int], y_coords: list[int], outline_color: ND_Color) -> None:
        #
        return

    #
    def draw_filled_polygon(self, x_coords: list[int], y_coords: list[int], fill_color: ND_Color) -> None:
        #
        return

    #
    def draw_textured_polygon(self, x_coords: list[int], y_coords: list[int], texture_id: int, texture_dx: int = 0, texture_dy: int = 0) -> None:
        #
        return

    #
    def draw_bezier_curve(self, x_coords: list[int], y_coords: list[int], line_color: ND_Color, nb_interpolations: int = 3) -> None:
        #
        return

    #
    def enable_area_drawing_constraints(self, x: int, y: int, width: int, height: int) -> None:
        #
        return

    #
    def disable_area_drawing_constraints(self) -> None:
        #
        return

    #
    def update_display(self) -> None:
        #
        return


#
class ND_EventsManager:
    #
    def __init__(self, main_app: ND_MainApp) -> None:
        #
        self.main_app: ND_MainApp = main_app
        #
        self.keys_pressed: set[str] = set()
        #
        self.events_waiting_too_poll: list[nd_event.ND_Event] = []
        #
        self.mouse_buttons_pressed: set[int] = set()

    #
    def is_shift_pressed(self) -> bool:
        #
        return "left shift" in self.keys_pressed or "right shift" in self.keys_pressed

    #
    def is_ctrl_pressed(self) -> bool:
        #
        return "left ctrl" in self.keys_pressed or "right ctrl" in self.keys_pressed

    #
    def is_alt_pressed(self) -> bool:
        #
        return "left alt" in self.keys_pressed

    #
    def is_alt_gr_pressed(self) -> bool:
        #
        return "right alt" in self.keys_pressed

    #
    def is_key_pressed(self, key_name: str) -> bool:
        return key_name in self.keys_pressed

    #
    def poll_next_event(self) -> Optional[nd_event.ND_Event]:
        return None

    #
    def get_mouse_position(self) -> ND_Point:
        #
        return ND_Point(0, 0)

    #
    def get_global_mouse_position(self) -> ND_Point:
        #
        return ND_Point(0, 0)


#
class ND_Val(int):
    #
    def __init__(self, value: int = 0, relative_from: int = -1) -> None:
        #
        self.value: int = value
        self.relative_from: int = -1

    #
    def get_value(self, relative_to: int = -1) -> int:
        #
        if relative_to == -1 or self.relative_from == -1:
            return self.value
        #
        return int(float(float(self.value) / float(self.relative_from)) * float(relative_to))


#
class ND_Elt:
    #
    def __init__(self, window: ND_Window, elt_id: str, position: ND_Position):
        #
        self.window: ND_Window = window
        #
        self.elt_id: str = elt_id
        #
        self.position: ND_Position = position
        #
        self.visible: bool = True
        self._visible: bool = True
        self.clickable: bool = True

    #
    @property
    def visible(self) -> bool:
        #
        if isinstance(self.position, ND_Position_Container):
            return self._visible and self.position.container.visible
        elif isinstance(self.position, ND_Position_MultiLayer):
            return self._visible and self.position.multilayer.visible
        else:
            return self._visible

    #
    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = value

    #
    def render(self) -> None:
        # Abstract class, so do nothing
        return

    #
    def handle_event(self, event) -> None:
        # Abstract class, so do nothing
        return

    #
    @property
    def x(self) -> int:
        #
        if not self.position:
            return 0
        #
        return self.position.x

    #
    @property
    def y(self) -> int:
        #
        if not self.position:
            return 0
        #
        return self.position.y

    #
    @property
    def w(self) -> int:
        #
        if not self.position:
            return 0
        #
        if self.min_w > 0 and self.position.w < self.min_w:
            return self.min_w
        #
        if self.max_w > 0 and self.position.w > self.max_w:
            return self.max_w
        #
        return self.position.w

    #
    @property
    def h(self) -> int:
        #
        if not self.position:
            return 0
        #
        if self.min_h > 0 and self.position.h < self.min_h:
            return self.min_h
        #
        if self.max_h > 0 and self.position.h > self.max_h:
            return self.max_h
        #
        return self.position.h

    #
    @property
    def min_w(self) -> int:
        #
        if not self.position or not hasattr(self.position, "get_min_width"):
            return 0
        #
        return self.position.get_min_width()

    #
    @property
    def max_w(self) -> int:
        #
        if not self.position or not hasattr(self.position, "get_max_width"):
            return 0
        #
        return self.position.get_max_width()

    #
    @property
    def min_h(self) -> int:
        #
        if not self.position or not hasattr(self.position, "get_max_height"):
            return 0
        #
        return self.position.get_max_height()

    #
    @property
    def max_h(self) -> int:
        #
        if not self.position or not hasattr(self.position, "get_max_height"):
            return 0
        #
        return self.position.get_max_height()

    #
    def get_margin_left(self, space_left: int = -1) -> int:
        #
        if not self.position or not hasattr(self.position, "get_margin_left"):
            return 0
        #
        return self.position.get_margin_left(space_left)

    #
    def get_margin_right(self, space_left: int = -1) -> int:
        #
        if not self.position or not hasattr(self.position, "get_margin_right"):
            return 0
        #
        return self.position.get_margin_right(space_left)

    #
    def get_margin_top(self, space_left: int = -1) -> int:
        #
        if not self.position or not hasattr(self.position, "get_margin_top"):
            return 0
        #
        return self.position.get_margin_top(space_left)

    #
    def get_margin_bottom(self, space_left: int = -1) -> int:
        #
        if not self.position or not hasattr(self.position, "get_margin_bottom"):
            return 0
        #
        return self.position.get_margin_bottom(space_left)

    #
    def get_width_stretch_ratio(self) -> float:
        #
        if not self.position or not hasattr(self.position, "get_width_stretch_ratio"):
            return 0
        #
        return self.position.get_width_stretch_ratio()

    #
    def get_height_stretch_ratio(self) -> float:
        #
        if not self.position or not hasattr(self.position, "get_height_stretch_ratio"):
            return 0
        #
        return self.position.get_height_stretch_ratio()


#
class ND_Quadtree:
    #
    def __init__(self,
                 x: Optional[int] = None,
                 y: Optional[int] = None,
                 width: Optional[int] = None,
                 height: Optional[int] = None,
                 max_objects: int = 10,
                 max_levels: int = 4,
                 level: int = 0) -> None:
        """Initialize the quadtree node with optional bounds and no fixed size."""

        #
        self.bounds: ND_Rect = ND_Rect(x or 0, y or 0, width or 0, height or 0)
        self.max_objects: int = max_objects
        self.max_levels: int = max_levels
        self.level: int = level
        self.objects: list[tuple[ND_Rect, str]] = []  # Now stores tuples of (rect, id)
        self.nodes: list['ND_Quadtree'] = []
        self.has_fixed_bounds: bool = x is not None and y is not None and width is not None and height is not None

    #
    def _expand(self, rect: ND_Rect) -> None:
        """Expand the quadtree boundaries to accommodate the new rect."""

        #
        if self.bounds.w == 0 and self.bounds.h == 0:
            # First insertion, establish the boundary with the size of the object
            self.bounds = ND_Rect(rect.x, rect.y, rect.w, rect.h)
            return

        # Expand the current bounds if the rect is outside
        new_x = min(self.bounds.x, rect.x)
        new_y = min(self.bounds.y, rect.y)
        new_right = max(self.bounds.x + self.bounds.w, rect.x + rect.w)
        new_bottom = max(self.bounds.y + self.bounds.h, rect.y + rect.h)

        new_width = new_right - new_x
        new_height = new_bottom - new_y

        # Create a new root that covers the expanded area
        new_bounds = ND_Rect(new_x, new_y, new_width, new_height)
        self._shift_and_expand(new_bounds)

    #
    def _shift_and_expand(self, new_bounds: ND_Rect) -> None:
        """Shift current tree and redistribute existing objects."""

        #
        self.bounds = new_bounds

        # If this was a non-empty quadtree, we need to reinsert the existing elements
        if self.objects or self.nodes:
            temp_objects = self.objects[:]
            self.objects.clear()

            # Reset the nodes and reinsert objects
            self.nodes.clear()
            for obj, obj_id in temp_objects:
                self.insert(obj, obj_id)

    #
    def subdivide(self) -> None:
        """Subdivide the current node into 4 quadrants."""

        #
        sub_width = self.bounds.w // 2
        sub_height = self.bounds.h // 2
        x, y = self.bounds.x, self.bounds.y

        self.nodes = [
            ND_Quadtree(x, y, sub_width, sub_height, self.max_objects, self.max_levels, self.level + 1),
            ND_Quadtree(x + sub_width, y, sub_width, sub_height, self.max_objects, self.max_levels, self.level + 1),
            ND_Quadtree(x, y + sub_height, sub_width, sub_height, self.max_objects, self.max_levels, self.level + 1),
            ND_Quadtree(x + sub_width, y + sub_height, sub_width, sub_height, self.max_objects, self.max_levels, self.level + 1)
        ]

    #
    def insert(self, rect: ND_Rect, obj_id: str) -> None:
        """Insert an object (with its id) into the quadtree, expanding it as needed."""

        #
        if not self.has_fixed_bounds:
            # If the quadtree is dynamically expanding, we may need to adjust the boundaries
            self._expand(rect)

        if self.nodes:
            # Insert into one of the sub-nodes if we are subdivided
            index = self.get_index(rect)
            if index != -1:
                self.nodes[index].insert(rect, obj_id)
                return

        # Otherwise, insert into this node
        self.objects.append((rect, obj_id))

        # If the number of objects exceeds the limit, subdivide if necessary
        if len(self.objects) > self.max_objects and self.level < self.max_levels:
            if not self.nodes:
                self.subdivide()

            i = 0
            while i < len(self.objects):
                obj_rect, obj_id = self.objects[i]
                index = self.get_index(obj_rect)
                if index != -1:
                    self.objects.pop(i)
                    self.nodes[index].insert(obj_rect, obj_id)
                else:
                    i += 1

    #
    def get_index(self, rect: ND_Rect) -> int:
        """Determine which quadrant the object belongs to in the current node."""

        #
        mid_x = self.bounds.x + self.bounds.w / 2
        mid_y = self.bounds.y + self.bounds.h / 2

        top = rect.y < mid_y
        bottom = rect.y + rect.h > mid_y
        left = rect.x < mid_x
        right = rect.x + rect.w > mid_x

        if top and right:
            return 1
        elif bottom and left:
            return 2
        elif bottom and right:
            return 3
        elif top and left:
            return 0
        return -1

    #
    def retrieve(self, rect: ND_Rect) -> list[tuple[ND_Rect, str]]:
        """Retrieve all objects that could collide with the given rect."""

        #
        result = self.objects[:]
        if self.nodes:
            index = self.get_index(rect)
            if index != -1:
                result.extend(self.nodes[index].retrieve(rect))
        return result

    #
    def get_colliding_ids(self, point: tuple[int, int]) -> list[str]:
        """Retrieve IDs of all elements colliding with a given point."""

        #
        point_rect = ND_Rect(point[0], point[1], 1, 1)  # Represent the point as a tiny rectangle
        potential_collisions = self.retrieve(point_rect)

        colliding_ids = []
        for obj_rect, obj_id in potential_collisions:
            if (obj_rect.x <= point[0] <= obj_rect.x + obj_rect.w and
                obj_rect.y <= point[1] <= obj_rect.y + obj_rect.h):
                colliding_ids.append(obj_id)
        return colliding_ids


#
class ND_Scene:
    #
    def __init__(
                    self,
                    window: ND_Window,
                    scene_id: str,
                    origin: ND_Point,
                    elements_layers: dict[int, dict[str, ND_Elt]] = {},
                    on_window_state: Optional[str | set[str]] = None
    ) -> None:

        # id
        self.scene_id: str = scene_id

        # ND_Scene origin
        self.origin: ND_Point = origin

        #
        self.on_window_state: Optional[str | set[str]] = on_window_state
        self.window: ND_Window = window
        self.on_window_state_test: Optional[Callable[[Optional[str]], bool]] = None
        #
        if self.on_window_state is not None:
            if isinstance(self.on_window_state, set):
                self.on_window_state_test = self.test_window_state_set
            else:
                self.on_window_state_test = self.test_window_state_str


        # list of elements sorted by render importance with layers (ascending order)
        self.elements_layers: dict[int, dict[str, ND_Elt]] = elements_layers
        self.collisions_layers: dict[int, ND_Quadtree] = {}
        self.elements_by_id: dict[str, ND_Elt] = {}

        #
        for layer in self.elements_layers:
            #
            self.collisions_layers[layer] = ND_Quadtree()
            #
            for element_id in self.elements_layers[layer]:
                #
                if element_id in self.elements_by_id:
                    raise UserWarning(f"Error: at least two elements have the same id: {element_id}!")
                #
                elt: ND_Elt = self.elements_layers[layer][element_id]
                #
                self.elements_by_id[element_id] = elt
                #
                self.collisions_layers[layer].insert(elt.position.rect, element_id)

        #
        self.layers_keys: list[int] = sorted(list(self.elements_layers.keys()))

    #
    def test_window_state_str(self, win_state: Optional[str]) -> bool:
        #
        return win_state != self.on_window_state

    #
    def test_window_state_set(self, win_state: Optional[str]) -> bool:
        #
        return win_state not in cast(set[str], self.on_window_state)

    #
    def handle_event(self, event) -> None:
        #
        if event.blocked:
            return
        #
        if self.on_window_state_test is not None and self.on_window_state_test(self.window.state):
            return

        #
        for elt in self.elements_by_id.values():

            #
            if hasattr(elt, "handle_event"):
                #
                elt.handle_event(event)

        # #
        # layer: int
        # for layer in self.layers_keys[::-1]:

        #     elt_list: list[str] = self.collisions_layers[layer].get_colliding_ids( (event.button.x, event.button.y) )

        #     for elt_id in elt_list:
        #         self.elements_by_id[elt_id].handle_event(event)

        #     if len(elt_list) > 0:
        #         return

    #
    def handle_window_resize(self) -> None:
        #
        if self.on_window_state_test is not None and self.on_window_state_test(self.window.state):
            # TODO: Optimisation
            pass

        #
        dict_elt: dict[str, ND_Elt]
        for dict_elt in self.elements_layers.values():
            #
            elt: ND_Elt
            for elt in dict_elt.values():
                if hasattr(elt, "update_layout"):
                    elt.update_layout()

    #
    def insert_to_layers_keys(self, layer_key: int) -> None:

        if ( len(self.layers_keys) == 0 ) or ( layer_key > self.layers_keys[-1] ):
            self.layers_keys.append(layer_key)
            return

        # Insertion inside a sorted list by ascendant
        i: int
        k: int
        for i, k in enumerate(self.layers_keys):
            if k > layer_key:
                self.layers_keys.insert(i, layer_key)
                return

    #
    def add_element(self, layer_id: int, elt: ND_Elt) -> None:
        #
        elt_id: str = elt.elt_id

        #
        if elt_id in self.elements_by_id:
            raise UserWarning(f"Error: at least two elements in the scene {self.scene_id} have the same id: {elt_id}!")

        #
        if layer_id not in self.elements_layers:
            self.elements_layers[layer_id] = {}
            self.collisions_layers[layer_id] = ND_Quadtree()
            self.insert_to_layers_keys(layer_id)

        #
        self.elements_layers[layer_id][elt_id] = elt
        self.elements_by_id[elt_id] = elt

        #
        self.collisions_layers[layer_id].insert(elt.position.rect, elt_id)

    #
    def render(self) -> None:
        #
        if self.on_window_state_test is not None and self.on_window_state_test(self.window.state):
            return
        #
        layer_key: int
        for layer_key in self.layers_keys:
            #
            element: ND_Elt
            for element in self.elements_layers[layer_key].values():
                element.render()


# ND_Text class implementation
class ND_Text(ND_Elt):
    #
    def __init__(
            self,
            window: ND_Window,
            elt_id: str,
            position: ND_Position,
            text: str,
            font_name: Optional[str] = None,
            font_size: int = 24,
            font_color: ND_Color = cl("gray"),
            text_wrap: bool = False,
            text_h_align: str = "center",
            text_v_align: str = "center"
        ) -> None:

        #
        super().__init__(window=window, elt_id=elt_id, position=position)
        self.text: str = text
        self.font_name: Optional[str] = font_name
        self.font_size: int = font_size
        self.font_color: ND_Color = font_color
        #
        self.text_wrap: bool = text_wrap
        #
        self.text_h_align: str = text_h_align
        self.text_v_align: str = text_v_align
        #
        self.base_text_w: int = 0
        self.base_text_h: int = 0
        #
        self.base_text_w, self.base_text_h = get_font_size(self.text, self.font_size, font_ratio=0.5)
        #

    #
    def render(self) -> None:
        #
        if not self.visible:
            return

        #
        x, y = self.x, self.y

        if self.w <= 0 or self.h <= 0:
            #
            # TODO: Taille indéterminée
            #
            pass
        else:
            #
            # TODO: Taille déterminée
            #
            if self.text_wrap:
                #
                # TODO: Calculer ce qui wrap ou pas
                #
                pass
            else:
                #
                if self.text_h_align == "center":
                    #
                    x=x + (self.w - self.base_text_w) // 2
                    #
                elif self.text_h_align == "right":
                    #
                    x=x + (self.w - self.base_text_w)
                    #
                #
                if self.text_v_align == "center":
                    #
                    y=y + (self.h - self.base_text_h) // 2
                    #
                elif self.text_v_align == "right":
                    #
                    y=y + (self.h - self.base_text_h)
                    #

        #
        self.window.draw_text(
                txt=self.text,
                x=x,
                y=y,
                font_name=self.font_name,
                font_size=self.font_size,
                font_color=self.font_color
        )


# ND_Clickable class implementation
class ND_Clickable(ND_Elt):
    #
    def __init__(
            self,
            window: ND_Window,
            elt_id: str,
            position: ND_Position,
            onclick: Optional[Callable[["ND_Clickable"], None]] = None,
            active: bool = True,
            block_events_below: bool = True
        ) -> None:

        #
        super().__init__(window=window, elt_id=elt_id, position=position)
        self.onclick: Optional[Callable[[ND_Clickable], None]] = onclick
        self.state: str = "normal"  # Can be "normal", "hover", or "clicked"
        self.mouse_bt_down_on_hover: bool = False
        self.block_events_below: bool = block_events_below
        #
        self.active: bool = active

    #
    def handle_event(self, event: nd_event.ND_Event) -> None:
        #
        if event.blocked:
            return
        #
        if not self.visible:
            self.state = "normal"
            return
        #
        if not self.clickable:
            self.state = "normal"
            return
        #
        if not self.active:
            self.state = "normal"
            return
        #
        if isinstance(event, nd_event.ND_EventMouseMotion):
            #
            if self.position.rect.contains_point(ND_Point(event.x, event.y)):
                self.state = "hover"
            else:
                self.state = "normal"
        #
        elif isinstance(event, nd_event.ND_EventMouseButtonDown):
            if event.button_id == 1:
                if self.position.rect.contains_point(ND_Point(event.x, event.y)):
                    #
                    self.state = "clicked"
                    #
                    self.mouse_bt_down_on_hover = True
                else:
                    self.mouse_bt_down_on_hover = False
        #
        elif isinstance(event, nd_event.ND_EventMouseButtonUp):
            if event.button_id == 1:
                #
                self.state = "hover" if self.position.rect.contains_point(ND_Point(event.x, event.y)) else "normal"
                #
                if self.state == "hover" and self.mouse_bt_down_on_hover:
                    #
                    if self.block_events_below:
                        event.blocked = True
                    #
                    if self.onclick:
                        self.onclick(self)
            #
            self.mouse_bt_down_on_hover = False


# ND_Rectangle class implementation
class ND_Rectangle(ND_Clickable):
    #
    def __init__(
            self,
            window: ND_Window,
            elt_id: str,
            position: ND_Position,
            border_radius: int = 5,
            border: bool = True,
            onclick: Optional[Callable] = None,
            mouse_active: bool = True,
            base_bg_color: Optional[ND_Color] = None,
            base_fg_color: Optional[ND_Color] = None,
            base_bg_texture: Optional[int | str] = None,
            hover_bg_color: Optional[ND_Color] = None,
            hover_fg_color: Optional[ND_Color] = None,
            hover_bg_texture: Optional[int | str] = None,
            clicked_bg_color: Optional[ND_Color] = None,
            clicked_fg_color: Optional[ND_Color] = None,
            clicked_bg_texture: Optional[int | str] = None
        ) -> None:

        #
        super().__init__(window=window, elt_id=elt_id, position=position, onclick=onclick, active=mouse_active)
        self.base_bg_color: ND_Color = base_bg_color if base_bg_color is not None else cl("gray")
        self.base_fg_color: ND_Color = base_fg_color if base_fg_color is not None else cl("black")
        self.base_bg_texture: Optional[int] = self.window.prepare_image_to_render(base_bg_texture) if isinstance(base_bg_texture, str) else base_bg_texture
        self.hover_bg_color: ND_Color = hover_bg_color if hover_bg_color is not None else cl("dark gray")
        self.hover_fg_color: ND_Color = hover_fg_color if hover_fg_color is not None else cl("black")
        self.hover_bg_texture: Optional[int] = self.window.prepare_image_to_render(hover_bg_texture) if isinstance(hover_bg_texture, str) else hover_bg_texture
        self.clicked_bg_color: ND_Color = clicked_bg_color if clicked_bg_color is not None else cl("very dark gray")
        self.clicked_fg_color: ND_Color = clicked_fg_color if clicked_fg_color is not None else cl("black")
        self.clicked_bg_texture: Optional[int] = self.window.prepare_image_to_render(clicked_bg_texture) if isinstance(clicked_bg_texture, str) else clicked_bg_texture
        #
        self.border: bool = border
        self.border_radius: int = border_radius
        #

    #
    def render(self) -> None:
        #
        if not self.visible:
            return

        #
        x, y = self.x, self.y

        #
        bg_color: ND_Color
        fg_color: ND_Color
        bg_texture: Optional[int]

        # Getting the right colors along the state
        if self.state == "normal":
            bg_color, fg_color, bg_texture = self.base_bg_color, self.base_fg_color, self.base_bg_texture
        elif self.state == "hover":
            bg_color, fg_color, bg_texture = self.hover_bg_color, self.hover_fg_color, self.hover_bg_texture
        else:  # clicked
            bg_color, fg_color, bg_texture = self.clicked_bg_color, self.clicked_fg_color, self.clicked_bg_texture

        # Drawing the background rect color or texture
        if bg_texture:
            self.window.render_prepared_texture(bg_texture, x, y, self.w, self.h)
        else:
            if not self.border and self.border_radius <= 0:
                self.window.draw_filled_rect(x, y, self.w, self.h, bg_color)
            elif not self.border:
                self.window.draw_rounded_rect(x, y, self.w, self.h, self.border_radius, bg_color, cl((0, 0, 0, 0)))
            else:
                self.window.draw_rounded_rect(x, y, self.w, self.h, self.border_radius, bg_color, fg_color)


# ND_Sprite class implementation
class ND_Sprite(ND_Clickable):
    #
    def __init__(
            self,
            window: ND_Window,
            elt_id: str,
            position: ND_Position,
            onclick: Optional[Callable] = None,
            mouse_active: bool = True,
            base_texture: Optional[int | str] = None,
            hover_texture: Optional[int | str] = None,
            clicked_texture: Optional[int | str] = None
        ) -> None:

        #
        super().__init__(window=window, elt_id=elt_id, position=position, onclick=onclick, active=mouse_active)
        self.base_texture: Optional[int | str] = base_texture
        self.hover_texture: Optional[int | str] = self.window.prepare_image_to_render(hover_texture) if isinstance(hover_texture, str) else hover_texture
        self.clicked_texture: Optional[int | str] = self.window.prepare_image_to_render(clicked_texture) if isinstance(clicked_texture, str) else clicked_texture
        #
        self.transformations: ND_Transformations = ND_Transformations()

    #
    def render(self) -> None:
        #
        if not self.visible:
            return

        #
        texture: Optional[int] = None

        # Getting the right colors along the state
        if self.state == "hover" and self.hover_texture is not None:
            if isinstance(self.hover_texture, str):
                self.hover_texture = self.window.prepare_image_to_render(self.hover_texture)
            #
            texture = self.hover_texture
        elif self.state == "clicked" and self.clicked_texture is not None:
            if isinstance(self.clicked_texture, str):
                self.clicked_texture = self.window.prepare_image_to_render(self.clicked_texture)
            #
            texture = self.clicked_texture
        #
        if texture is None:
            if isinstance(self.base_texture, str):
                self.base_texture = self.window.prepare_image_to_render(self.base_texture)
            #
            texture = self.base_texture

        # Drawing the background rect color or texture
        if texture is not None:
            # print(f"DEBUG | rendering texture id {texture} at x={self.x}, y={self.y}, w={self.w}, h={self.h}")
            self.window.render_prepared_texture(texture, self.x, self.y, self.w, self.h, self.transformations)


#
class ND_AtlasTexture:
    #
    def __init__(self, window: ND_Window, texture_atlas_path: str, tiles_size: ND_Point = ND_Point(32, 32)) -> None:
        #
        self.window: ND_Window = window
        #
        self.texture_atlas_path: str = texture_atlas_path
        #
        self.texture_atlas: Optional[int] = None
        #
        self.tiles_size: ND_Point = tiles_size
        self.texture_dim: ND_Point = ND_Point(-1, -1)

    #
    def render_texture_at_position(self,
                                    at_win_x: int, at_win_y: int, at_win_w: int, at_win_h: int,
                                    tile_x: int, tile_y: int, nb_tiles_w: int = 1, nb_tiles_h: int = 1,
                                    transformations: ND_Transformations = ND_Transformations()
        ) -> None:

        #
        if self.texture_atlas is None:
            #
            self.texture_atlas = self.window.prepare_image_to_render(self.texture_atlas_path)
            self.texture_dim = self.window.get_prepared_texture_size(self.texture_atlas)

        #
        src_x: int = self.tiles_size.x * tile_x
        src_y: int = self.tiles_size.y * tile_y
        src_w: int = self.tiles_size.x * nb_tiles_w
        src_h: int = self.tiles_size.y * nb_tiles_h

        #
        src_x = clamp(src_x, 0, self.texture_dim.x)
        src_y = clamp(src_y, 0, self.texture_dim.y)
        src_w = clamp(src_w, 0, self.texture_dim.x-src_x)
        src_h = clamp(src_h, 0, self.texture_dim.y-src_y)

        #
        self.window.render_part_of_prepared_texture(
                self.texture_atlas,
                at_win_x, at_win_y, at_win_w, at_win_h,
                src_x, src_y, src_w, src_h,
                transformations
        )


#
class ND_Sprite_of_AtlasTexture(ND_Elt):
    #
    def __init__(
            self,
            window: ND_Window,
            elt_id: str,
            position: ND_Position,
            atlas_texture: ND_AtlasTexture,
            tile_x: int,
            tile_y: int,
            nb_tiles_x: int = 1,
            nb_tiles_y: int = 1
        ) -> None:
        #
        super().__init__(window, elt_id, position)
        #
        self.atlas_texture: ND_AtlasTexture = atlas_texture
        #
        self.tile_x: int = tile_x
        self.tile_y: int = tile_y
        self.nb_tiles_x: int = nb_tiles_x
        self.nb_tiles_y: int = nb_tiles_y
        #
        self.transformations: ND_Transformations = ND_Transformations()

    #
    def render(self) -> None:
        #
        self.atlas_texture.render_texture_at_position(
                self.x, self.y, self.w, self.h,
                self.tile_x, self.tile_y, self.nb_tiles_x, self.nb_tiles_y,
                self.transformations
        )


# ND_Sprite class implementation
class ND_AnimatedSprite(ND_Elt):
    #
    def __init__(
            self,
            window: ND_Window,
            elt_id: str,
            position: ND_Position,
            animations: dict[str, list[int | ND_Sprite_of_AtlasTexture]],
            animations_speed: dict[str, float],
            default_animation_speed: float = 0.1,
            default_animation: str = ""
        ) -> None:

        #
        super().__init__(window=window, elt_id=elt_id, position=position)
        #
        self.animations: dict[str, list[Any]] = animations
        self.animations_speed: dict[str, float] = animations_speed
        #
        self.default_animation_speed: float = default_animation_speed
        #
        self.transformations: ND_Transformations = ND_Transformations()
        #
        self.current_animation: str = default_animation
        self.current_frame: int = 0
        self.delta_shift_time: float = 0
        self.last_update: float = time.time()
        #

    #
    def add_animation(self, animation_name: str, animation: list[int | ND_Sprite_of_AtlasTexture], animation_speed: float = -1, if_exists: str = "error") -> None:
        #
        if animation_name in self.animations:
            #
            if if_exists == "ignore":
                #
                return
            #
            elif if_exists == "error":
                #
                raise UserWarning(f"Error: tried to add animation \"{animation_name}\" but it already existed in AnimatedSprite {self.elt_id}")
        #
        self.animations[animation_name] = animation
        #
        if animation_speed > 0:
            self.animations_speed[animation_name] = animation_speed

    #
    def add_frame_to_animation(self, animation_name: str, animation_frame: int | ND_Sprite_of_AtlasTexture, if_not_exists: str = "create") -> None:
        #
        if animation_name not in self.animations:
            #
            if if_not_exists == "create":
                #
                self.animations[animation_name] = []
            #
            elif if_not_exists == "ignore":
                #
                return
            #
            elif if_not_exists == "error":
                #
                raise UserWarning(f"Error: tried to add a frame to animation \"{animation_name}\" but it doesn't exist in AnimatedSprite {self.elt_id}")
        #
        self.animations[animation_name].append(animation_frame)

    #
    def set_animation_speed(self, animation_name: str, animation_speed: float) -> None:
        #
        self.animations_speed[animation_name] = animation_speed

    #
    def change_animation(self, new_animation_name: str) -> None:
        #
        self.current_animation = new_animation_name
        #
        self.current_frame = 0
        self.last_update = time.time()

    #
    def render(self) -> None:
        #
        if not self.visible:
            return

        #
        if self.current_animation not in self.animations:
            return

        #
        an_speed: float = self.default_animation_speed
        if self.current_animation in self.animations_speed:
            an_speed = self.animations_speed[self.current_animation]

        #
        t_now: float = time.time()
        #
        if t_now - self.last_update >= an_speed:
            #
            self.last_update = t_now
            #
            self.current_frame = (self.current_frame + 1) % (len(self.animations[self.current_animation]))

        #
        current_frame: Optional[int | ND_Sprite_of_AtlasTexture] = self.animations[self.current_animation][self.current_frame]

        # Drawing the background rect color or texture
        if current_frame is not None:
            #
            if isinstance(current_frame, int):
                #
                self.window.render_prepared_texture(current_frame, self.x, self.y, self.w, self.h, self.transformations)
            else:
                #
                old_position: ND_Position = current_frame.position
                old_transformations: ND_Transformations = current_frame.transformations
                #
                current_frame.position = self.position
                current_frame.transformations = self.transformations + current_frame.transformations
                #
                current_frame.render()
                #
                current_frame.position = old_position
                current_frame.transformations = old_transformations


# ND_Button class implementation
class ND_Button(ND_Clickable):

    #
    def __init__(
            self,
            window: ND_Window,
            elt_id: str,
            position: ND_Position,
            onclick: Optional[Callable[[ND_Clickable], None]],
            text: str,
            mouse_active: bool = True,
            font_name: Optional[str] = None,
            font_size: int = 24,
            border_radius: int = 5,
            border: bool = True,
            base_bg_color: Optional[ND_Color] = None,
            base_fg_color: Optional[ND_Color] = None,
            base_bg_texture: Optional[int | str] = None,
            hover_bg_color: Optional[ND_Color] = None,
            hover_fg_color: Optional[ND_Color] = None,
            hover_bg_texture: Optional[int | str] = None,
            clicked_bg_color: Optional[ND_Color] = None,
            clicked_fg_color: Optional[ND_Color] = None,
            clicked_bg_texture: Optional[int | str] = None,
            texture_transformations: ND_Transformations = ND_Transformations()
        ) -> None:

        #
        super().__init__(window=window, elt_id=elt_id, position=position, onclick=onclick, active=mouse_active)
        self.text: str = text
        self.font_name: Optional[str] = font_name
        self.font_size: int = font_size
        self.base_bg_color: ND_Color = base_bg_color if base_bg_color is not None else cl("gray")
        self.base_fg_color: ND_Color = base_fg_color if base_fg_color is not None else cl("black")
        self.base_bg_texture: Optional[int] = self.window.prepare_image_to_render(base_bg_texture) if isinstance(base_bg_texture, str) else base_bg_texture
        self.hover_bg_color: ND_Color = hover_bg_color if hover_bg_color is not None else cl("dark gray")
        self.hover_fg_color: ND_Color = hover_fg_color if hover_fg_color is not None else cl("black")
        self.hover_bg_texture: Optional[int] = self.window.prepare_image_to_render(hover_bg_texture) if isinstance(hover_bg_texture, str) else hover_bg_texture
        self.clicked_bg_color: ND_Color = clicked_bg_color if clicked_bg_color is not None else cl("very dark gray")
        self.clicked_fg_color: ND_Color = clicked_fg_color if clicked_fg_color is not None else cl("black")
        self.clicked_bg_texture: Optional[int] = self.window.prepare_image_to_render(clicked_bg_texture) if isinstance(clicked_bg_texture, str) else clicked_bg_texture
        #
        self.border: bool = border
        self.border_radius: int = border_radius
        #
        self.base_text_w: int = 0
        self.base_text_h: int = 0
        #
        self.base_text_w, self.base_text_h = get_font_size(self.text, self.font_size, font_ratio=0.5)
        #
        self.texture_transformations: ND_Transformations = texture_transformations

    #
    def render(self) -> None:
        #
        if not self.visible:
            return

        #
        x, y = self.x, self.y

        #
        bg_color: ND_Color
        fg_color: ND_Color
        bg_texture: Optional[int]

        # Getting the right colors along the state
        if self.state == "normal":
            bg_color, fg_color, bg_texture = self.base_bg_color, self.base_fg_color, self.base_bg_texture
        elif self.state == "hover":
            bg_color, fg_color, bg_texture = self.hover_bg_color, self.hover_fg_color, self.hover_bg_texture if self.hover_bg_texture is not None else self.base_bg_texture
        else:  # clicked
            bg_color, fg_color, bg_texture = self.clicked_bg_color, self.clicked_fg_color, self.clicked_bg_texture if self.clicked_bg_texture is not None else self.base_bg_texture

        # Drawing the background rect color or texture
        if bg_texture:
            self.window.render_prepared_texture(bg_texture, x, y, self.w, self.h, transformations=self.texture_transformations)
        else:
            if not self.border and self.border_radius <= 0:
                self.window.draw_filled_rect(x, y, self.w, self.h, bg_color)
            elif not self.border:
                self.window.draw_rounded_rect(x, y, self.w, self.h, self.border_radius, bg_color, cl((0, 0, 0, 0)))
            else:
                self.window.draw_rounded_rect(x, y, self.w, self.h, self.border_radius, bg_color, fg_color)

        #
        self.window.draw_text(
                txt=self.text,
                x=x + (self.w - self.base_text_w) // 2,
                y=y + (self.h - self.base_text_h) // 2,
                font_name=self.font_name,
                font_size=self.font_size,
                font_color=fg_color
        )


# ND_H_ScrollBar class implementation
class ND_H_ScrollBar(ND_Elt):
    #
    def __init__(
                    self,
                    window: ND_Window,
                    elt_id: str,
                    position: ND_Position,
                    content_width: int,
                    bg_cl: ND_Color = cl((10, 10, 10)),
                    fg_cl: ND_Color = cl("white"),
                    on_value_changed: Optional[Callable[["ND_H_ScrollBar", float], None]] = None
        ) -> None:
        #
        super().__init__(window=window, elt_id=elt_id, position=position)
        #
        self.on_value_changed: Optional[Callable[[ND_H_ScrollBar, float], None]] = on_value_changed
        #
        self.content_width: int = content_width
        self.scroll_position: float = 0
        self.dragging: bool = False
        self.prep_dragging: bool = False
        #
        self.bg_cl: ND_Color = bg_cl
        self.fg_cl: ND_Color = fg_cl

    #
    def get_scroll_ratio(self) -> float:
        #
        return self.scroll_position / float(self.content_width)

    #
    @property
    def thumb_width(self) -> int:
        return max(20, int(self.w * (self.w / self.content_width)))

    #
    def render(self) -> None:
        #
        if not self.visible:
            return

        # Draw background
        self.window.draw_filled_rect(self.x, self.y, self.w, self.h, self.bg_cl)
        #
        self.window.draw_unfilled_rect(self.x, self.y, self.w, self.h, self.fg_cl)

        # Draw thumb
        thumb_x = self.x + int(self.scroll_position * (self.w - self.thumb_width) / (self.content_width - self.w))
        self.window.draw_filled_rect(thumb_x, self.y, self.thumb_width, self.h, self.fg_cl)

    #
    def handle_event(self, event: nd_event.ND_Event) -> None:
        #
        if event.blocked:
            return
        #
        if isinstance(event, nd_event.ND_EventMouse):
            #
            if not self.position.rect.contains_point(ND_Point(event.x, event.y)):
                self.prep_dragging = False
                self.dragging = False
                return
            #
            if isinstance(event, nd_event.ND_EventMouseButtonDown):
                if event.button_id == 1:
                    self.prep_dragging = True
            #
            elif isinstance(event, nd_event.ND_EventMouseButtonUp):
                if event.button_id == 1:
                    if self.dragging:
                        self.dragging = False
                    else:
                        relative_x = event.x - self.x
                        self.scroll_position = max(0, min(self.content_width - self.w,
                                                    int(relative_x * self.content_width / self.w)))
                        #
                        if self.on_value_changed is not None:
                            self.on_value_changed(self, self.scroll_position)

            #
            elif isinstance(event, nd_event.ND_EventMouseMotion):
                if self.dragging or self.prep_dragging:
                    #
                    if self.prep_dragging:
                        self.dragging = True
                        self.prep_dragging = False
                    #
                    relative_x = event.x - self.x
                    self.scroll_position = max(0, min(self.content_width - self.w,
                                                    int(relative_x * self.content_width / self.w)))
                    #
                    if self.on_value_changed is not None:
                        self.on_value_changed(self, self.scroll_position)


# ND_V_ScrollBar class implementation
class ND_V_ScrollBar(ND_Elt):
    #
    def __init__(
                    self,
                    window: ND_Window,
                    elt_id: str,
                    position: ND_Position,
                    content_height: int,
                    fg_color: ND_Color = cl("white"),
                    bg_color: ND_Color = cl("dark gray"),
                    on_value_changed: Optional[Callable[["ND_V_ScrollBar", float], None]] = None
        ) -> None:
        #
        super().__init__(window=window, elt_id=elt_id, position=position)
        #
        self.on_value_changed: Optional[Callable[[ND_V_ScrollBar, float], None]] = on_value_changed
        #
        self.content_height = content_height
        self.scroll_position = 0
        self.dragging = False
        #
        self.fg_color: ND_Color = fg_color
        self.bg_color: ND_Color = bg_color

    #
    def get_scroll_ratio(self) -> float:
        #
        return self.scroll_position / float(self.content_height)

    @property
    def thumb_height(self) -> int:
        return clamp(int(self.w * (self.w / self.content_height)), 2, 20)

    #
    def render(self) -> None:
        if not self.visible:
            return

        # Draw background
        self.window.draw_filled_rect(self.x, self.y, self.w, self.h, self.bg_color)

        # Draw thumb
        thumb_y = self.y + int(self.scroll_position * (self.h - self.thumb_height) / (self.content_height))
        self.window.draw_filled_rect(self.x, thumb_y, self.w, self.thumb_height, self.fg_color)

    #
    def handle_event(self, event: nd_event.ND_Event) -> None:
        #
        if event.blocked:
            return
        #
        if isinstance(event, nd_event.ND_EventMouseButtonDown):
            if event.button_id == 1:
                if self.position.rect.contains_point(ND_Point(event.x, event.y)):
                    #
                    self.scroll_position = clamp(int(((event.y - self.y) / self.h) * self.content_height), 0, self.content_height)
                    #
                    if self.on_value_changed is not None:
                        self.on_value_changed(self, self.scroll_position)
                    #
                    event.blocked = True
                    #
                    self.dragging = True
                else:
                    self.dragging = False
        #
        elif isinstance(event, nd_event.ND_EventMouseButtonUp):
            if event.button_id == 1:
                self.dragging = False
        #
        elif isinstance(event, nd_event.ND_EventMouseMotion):
            if self.dragging:
                relative_y = event.y - self.y
                self.scroll_position = max(0, min(self.content_height - self.h,
                                                int(relative_y * self.content_height / self.h)))
                #
                if self.on_value_changed is not None:
                    self.on_value_changed(self, self.scroll_position)


#
class ND_LineEdit(ND_Elt):
    def __init__(
        self,
        window: ND_Window,
        elt_id: str,
        position: ND_Position,
        text: str = "",
        place_holder: str = "",
        max_text_length: int = -1,
        mouse_active: bool = True,
        font_name: Optional[str] = None,
        font_size: int = 24,
        border_radius: int = 5,
        border: bool = True,
        base_bg_color: Optional[ND_Color] = None,
        base_fg_color: Optional[ND_Color] = None,
        hover_bg_color: Optional[ND_Color] = None,
        hover_fg_color: Optional[ND_Color] = None,
        clicked_bg_color: Optional[ND_Color] = None,
        clicked_fg_color: Optional[ND_Color] = None,
        characters_restrictions: Optional[set[str]] = None,
        password_mode: bool = False,
        on_line_edit_validated: Optional[Callable[["ND_LineEdit", str], None]] = None,
        on_line_edit_escaped: Optional[Callable[["ND_LineEdit"], None]] = None
    ) -> None:
        super().__init__(window=window, elt_id=elt_id, position=position)
        self.state: str = "normal"
        self.text: str = text
        self.place_holder: str = place_holder
        self.font_name: Optional[str] = font_name
        self.font_size: int = font_size
        self.base_bg_color: ND_Color = base_bg_color if base_bg_color else cl("gray")
        self.base_fg_color: ND_Color = base_fg_color if base_fg_color else cl("black")
        self.hover_bg_color: ND_Color = hover_bg_color if hover_bg_color else cl("dark gray")
        self.hover_fg_color: ND_Color = hover_fg_color if hover_fg_color else cl("black")
        self.clicked_bg_color: ND_Color = clicked_bg_color if clicked_bg_color else cl("very dark gray")
        self.clicked_fg_color: ND_Color = clicked_fg_color if clicked_fg_color else cl("black")
        self.border: bool = border
        self.border_radius: int = border_radius
        self.cursor: int = len(text)
        self.cursor_width: int = 2
        self.cursor_height: int = self.font_size
        self.focused: bool = False
        self.max_text_length: int = max_text_length
        self.characters_restrictions: Optional[set[str]] = characters_restrictions   # Do not accept others character that theses
        self.password_mode: bool = password_mode
        self.on_line_edit_validated: Optional[Callable[[ND_LineEdit, str], None]] = on_line_edit_validated
        self.on_line_edit_escaped: Optional[Callable[[ND_LineEdit], None]] = on_line_edit_escaped

        # Scrollbar-related
        self.scrollbar_height: int = 10
        self.full_text_width: int = 0
        self.scroll_offset: int = 0
        self.scrollbar: ND_H_ScrollBar = ND_H_ScrollBar(
            window = self.window,
            elt_id = f"scrollbar_{self.elt_id}",
            position = ND_Position(self.x, self.y + self.h - self.scrollbar_height, self.w, self.scrollbar_height),
            content_width = self.window.get_text_size_with_font(self.text, self.font_size, self.font_name).x
        )

    #
    def set_text(self, txt: str) -> None:
        #
        self.text = txt
        self.cursor = len(self.text)

    #
    def render(self) -> None:
        if not self.visible:
            return

        # Determine background and text color based on the state
        bg_color = self.base_bg_color
        fg_color = self.base_fg_color
        if self.state == "hover":
            bg_color = self.hover_bg_color
            fg_color = self.hover_fg_color
        elif self.state == "clicked":
            bg_color = self.clicked_bg_color
            fg_color = self.clicked_fg_color

        # Draw the background rectangle
        if self.border:
            self.window.draw_rounded_rect(
                self.x, self.y, self.w, self.h, self.border_radius, bg_color, fg_color
            )
        else:
            self.window.draw_filled_rect(self.x, self.y, self.w, self.h, bg_color)

        # Determine the visible portion of the text
        render_text = self.text if self.text else self.place_holder
        text_color = fg_color if self.text else cl("light gray")

        self.full_text_width = self.window.get_text_size_with_font(render_text, self.font_size, self.font_name).x

        #
        if self.scrollbar.scroll_position > 0:
            size_hidden: int
            count_hidden: int
            size_hidden, count_hidden = self.window.get_count_of_renderable_chars_fitting_given_width(txt=render_text, given_width=int(self.scrollbar.scroll_position), font_name=self.font_name, font_size=self.font_size)
            #
            if count_hidden > 0:
                render_text = render_text[count_hidden:]
                self.scroll_offset = int(self.scrollbar.scroll_position) - size_hidden
        else:
            self.scroll_offset = 0

        visible_text = render_text

        visible_text_width: int = self.full_text_width
        if self.full_text_width > self.w:
            while visible_text_width > self.w:
                visible_text = visible_text[1:]
                visible_text_width = self.window.get_text_size_with_font(visible_text, self.font_size, self.font_name).x

        # TODO: correct the text that is displayed and visible


        # Render the text
        self.window.draw_text(
            txt=visible_text,
            x=self.x + 5 - self.scroll_offset,
            y=self.y + (self.h - self.cursor_height) // 2,
            font_size=self.font_size,
            font_color=text_color,
            font_name=self.font_name,
        )

        # Render the cursor if focused
        if self.focused and len(self.text) >= self.cursor:

            txt_before_cursor_width: int = self.window.get_text_size_with_font(self.text[: self.cursor], self.font_size, self.font_name).x

            cursor_x = self.x + 5 + txt_before_cursor_width - self.scroll_offset
            self.window.draw_filled_rect(cursor_x, self.y + 5, self.cursor_width, self.cursor_height, fg_color)

        # Render horizontal scrollbar if necessary
        if self.full_text_width > self.w:
            self.scrollbar.render()

    #
    def write(self, char: str) -> None:
        #
        if self.max_text_length > 0 and len(self.text) + len(char) > self.max_text_length:
            return
        #
        self.text = self.text[: self.cursor] + char + self.text[self.cursor :]
        self.cursor += len(char)
        #
        self.full_text_width = self.window.get_text_size_with_font(self.text, self.font_size, self.font_name).x
        self.scrollbar.content_width = self.full_text_width

    #
    def print_debug_infos(self) -> None:
        #
        print(f"\nDEBUG | line_edit={self.elt_id} | visible={self.visible} | focused={self.focused} | text={self.text} | cursor={self.cursor} | full_text_width={self.full_text_width} | scroll_position={self.scrollbar.scroll_position}\n")

    #
    def handle_event(self, event: nd_event.ND_Event) -> None:
        #
        if event.blocked:
            return
        #
        if isinstance(event, nd_event.ND_EventKeyDown) and event.key == "F3":
            self.print_debug_infos()
        #
        if not self.visible:
            return
        #
        if isinstance(event, nd_event.ND_EventMouse):
            if event.x >= self.x and event.x <= self.x + self.w and event.y >= self.y and event.y <= self.y + self.h:
                if isinstance(event, nd_event.ND_EventMouseButtonDown):
                    if self.state == "clicked":
                        # TODO: move the cursor to the closest place possible of the click
                        pass
                    else:
                        self.state = "clicked"
                        self.focused = True
                elif isinstance(event, nd_event.ND_EventMouseMotion):
                    self.state = "hover"
            elif isinstance(event, nd_event.ND_EventMouseButtonDown):
                self.state = "normal"
                self.focused = False
                #
                if self.on_line_edit_escaped is not None:
                    self.on_line_edit_escaped(self)
            else:
                self.state = "normal"

            # Delegate scrollbar events
            if self.full_text_width > self.w:
                self.scrollbar.handle_event(event)
                self.scroll_offset = int(self.scrollbar.get_scroll_ratio() * (self.full_text_width - self.w))

        elif isinstance(event, nd_event.ND_EventKeyDown) and self.focused:
            #
            shift_pressed: bool = self.window.main_app.events_manager.is_shift_pressed()
            #
            # TODO: complete with all the keys, for instance the numpad keys, etc...
            if event.key == "escape":
                self.state = "normal"
                self.focused = False
                #
                if self.on_line_edit_escaped is not None:
                    self.on_line_edit_escaped(self)
            elif event.key == "return":
                self.state = "normal"
                self.focused = False
                #
                if self.on_line_edit_validated is not None:
                    self.on_line_edit_validated(self, self.text)
            #
            elif event.key == "backspace" and self.cursor > 0:
                self.text = self.text[: self.cursor - 1] + self.text[self.cursor :]
                self.cursor -= 1
                self.full_text_width = self.window.get_text_size_with_font(self.text, self.font_size, self.font_name).x
                self.scrollbar.content_width = self.full_text_width
            #
            elif event.key == "left arrow" and self.cursor > 0:
                self.cursor -= 1
            #
            elif event.key == "right arrow" and self.cursor < len(self.text):
                self.cursor += 1
                text_width = self.window.get_text_size_with_font(self.text[:self.cursor], self.font_size, self.font_name).x
                if text_width - self.scroll_offset > self.w:
                    self.scroll_offset = text_width - self.w
            #
            elif len(event.key) == 1:
                if shift_pressed:
                    self.write(event.key.upper())
                else:
                    self.write(event.key)
            #
            elif event.key == "espace":
                self.write(" ")
            #
            elif event.key == "semicolon":
                if shift_pressed:
                    self.write(".")
                else:
                    self.write(",")

            # Update scrollbar position
            if self.full_text_width > self.w:
                self.scrollbar.scroll_position = self.scroll_offset / (self.full_text_width - self.w)
            #
            # print(f"DEBUG | event = {event}")
            # self.print_debug_infos()


# ND_Checkbox
class ND_Checkbox(ND_Elt):
    def __init__(
        self,
        window: ND_Window,
        elt_id: str,
        position: ND_Position,
        checked: bool = False,
        on_pressed: Optional[Callable[["ND_Checkbox"], None]] = None
    ) -> None:
        #
        super().__init__(window=window, elt_id=elt_id, position=position)
        #
        self.on_pressed: Optional[Callable[["ND_Checkbox"], None]] = on_pressed
        #
        self.checked: bool = checked
        #
        self.bt_checked: ND_Button = ND_Button(
            window=self.window,
            elt_id=f"{self.elt_id}_bt_checked",
            position=self.position,
            onclick=self.on_bt_checked_pressed,
            text="v",
            base_fg_color=cl("dark green"),
            hover_fg_color=cl("green")
            # TODO: style
        )
        #
        self.bt_unchecked: ND_Button = ND_Button(
            window=self.window,
            elt_id=f"{self.elt_id}_bt_unchecked",
            position=self.position,
            onclick=self.on_bt_unchecked_pressed,
            text="x",
            base_fg_color=cl("dark red"),
            hover_fg_color=cl("red")
            # TODO: style
        )

    #
    def render(self) -> None:
        if self.checked:
            self.bt_checked.render()
        else:
            self.bt_unchecked.render()

    #
    def on_bt_checked_pressed(self, _) -> None:
        #
        self.checked = False
        #
        self.bt_checked.visible = False
        self.bt_unchecked.visible = True
        #
        if self.on_pressed is not None:
            self.on_pressed(self)

    #
    def on_bt_unchecked_pressed(self, _) -> None:
        #
        self.checked = True
        #
        self.bt_checked.visible = True
        self.bt_unchecked.visible = False
        #
        if self.on_pressed is not None:
            self.on_pressed(self)

    #
    def is_checked(self) -> bool:
        return self.checked

    #
    def handle_event(self, event: nd_event.ND_Event) -> None:
        #
        if event.blocked:
            return
        #
        if not self.visible:
            return
        #
        if self.checked:
            self.bt_checked.handle_event(event)
        else:
            self.bt_unchecked.handle_event(event)


# ND_NumberInput
class ND_NumberInput(ND_Elt):
    def __init__(
        self,
        window: ND_Window,
        elt_id: str,
        position: ND_Position,
        value: float = 0,
        min_value: float = 0,
        max_value: float = 100,
        step: float = 1,
        digits_after_comma: int = 0,
        on_new_value_validated: Optional[Callable[["ND_NumberInput", float], None]] = None
    ) -> None:
        #
        super().__init__(window=window, elt_id=elt_id, position=position)
        #
        self.on_new_value_validated: Optional[Callable[["ND_NumberInput", float], None]] = on_new_value_validated
        #
        self.min_value: float = min_value
        self.max_value: float = max_value
        self.step: float = step
        self.digits_after_comma: int = digits_after_comma
        if self.digits_after_comma > 0:
            self.value = round(clamp(value, self.min_value, self.max_value), self.digits_after_comma)
        else:
            self.value = int(clamp(value, self.min_value, self.max_value))
        #
        self.main_row_container: ND_Container = ND_Container(
            window=self.window,
            elt_id=f"{self.elt_id}_main_row_container",
            position=self.position,
            element_alignment="row"
        )
        #
        self.line_edit: ND_LineEdit = ND_LineEdit(
            window=self.window,
            elt_id=f"{self.elt_id}_line_edit",
            position=ND_Position_Container(w="80%", h="100%", container=self.main_row_container),
            text=str(self.value),
            place_holder="value",
            font_name="FreeSans",
            font_size=24,
            on_line_edit_escaped=self.on_line_edit_escaped,
            on_line_edit_validated=self.on_line_edit_validated
        )
        #
        self.main_row_container.add_element(self.line_edit)
        #
        self.col_bts_container: ND_Container = ND_Container(
            window=self.window,
            elt_id=f"{self.elt_id}_col_bts_container",
            position=ND_Position_Container(w="20%", h="100%", container=self.main_row_container)
        )
        self.main_row_container.add_element(self.col_bts_container)
        #
        self.bt_up: ND_Button = ND_Button(
            window=self.window,
            elt_id=f"{self.elt_id}_bt_up",
            position=ND_Position_Container(w="100%", h="50%", container=self.col_bts_container),
            onclick=self.on_bt_up_pressed,
            text="^",
            font_name="FreeSans",
            font_size=12
        )
        self.col_bts_container.add_element(self.bt_up)
        #
        self.bt_down: ND_Button = ND_Button(
            window=self.window,
            elt_id=f"{self.elt_id}_bt_down",
            position=ND_Position_Container(w="100%", h="50%", container=self.col_bts_container),
            onclick=self.on_bt_down_pressed,
            text="v",
            font_name="FreeSans",
            font_size=12
        )
        self.col_bts_container.add_element(self.bt_down)

    #
    def update_layout(self) -> None:
        self.main_row_container.update_layout()

    #
    def render(self) -> None:
        #
        if not self.visible:
            return
        #
        self.main_row_container.render()
        #

    #
    def handle_event(self, event: nd_event.ND_Event) -> None:
        #
        if event.blocked:
            return
        #
        self.line_edit.handle_event(event)
        self.bt_up.handle_event(event)
        self.bt_down.handle_event(event)

    #
    def on_bt_up_pressed(self, _) -> None:
        #
        new_value: float = self.value + self.step
        #
        if self.digits_after_comma > 0:
            self.value = round(clamp(new_value, self.min_value, self.max_value), self.digits_after_comma)
        else:
            self.value = int(clamp(new_value, self.min_value, self.max_value))
        #
        self.line_edit.set_text(str(self.value))

    #
    def on_bt_down_pressed(self, _) -> None:
        #
        new_value: float = self.value - self.step
        #
        if self.digits_after_comma > 0:
            self.value = round(clamp(new_value, self.min_value, self.max_value), self.digits_after_comma)
        else:
            self.value = int(clamp(new_value, self.min_value, self.max_value))
        #
        self.line_edit.set_text(str(self.value))

    #
    def on_line_edit_validated(self, _, value: str) -> None:
        #
        try:
            new_value: float = float(self.line_edit.text)
            #
            if self.digits_after_comma > 0:
                self.value = round(clamp(new_value, self.min_value, self.max_value), self.digits_after_comma)
            else:
                self.value = int(clamp(new_value, self.min_value, self.max_value))
        except Exception as _:
            pass
        finally:
            self.line_edit.set_text(str(self.value))
            #
            if self.on_new_value_validated is not None:
                #
                self.on_new_value_validated(self, self.value)

    #
    def on_line_edit_escaped(self, _) -> None:
        #
        value: str = self.line_edit.text
        #
        self.on_line_edit_validated(_, value)
        #
        # self.line_edit.set_text(str(self.value))


# ND_SelectOptions
class ND_SelectOptions(ND_Elt):
    def __init__(
        self,
        window: ND_Window,
        elt_id: str,
        position: ND_Position,
        value: str,
        options: set[str],
        option_list_buttons_height: int = 300,
        on_value_selected: Optional[Callable[["ND_SelectOptions", str], None]] = None,
        font_size: int = 24,
        font_name: Optional[str] = None
    ) -> None:
        #
        super().__init__(window=window, elt_id=elt_id, position=position)
        #
        self.font_name: Optional[str] = font_name
        self.font_size: int = font_size
        #
        self.on_value_selected: Optional[Callable[[ND_SelectOptions, str], None]] = on_value_selected
        #
        self.value: str = value
        self.options: set[str] = options
        #
        self.options_bts: dict[str, ND_Button] = {}
        #
        self.option_list_buttons_height: int = option_list_buttons_height
        #
        self.state: str = "base"  # "base" or "selection"
        #
        # 1st side: the main button to show which element is selected, and if clicked, hide itself and show the 2nd part of it
        #
        self.main_button: ND_Button = ND_Button(
            window=self.window,
            elt_id=f"{self.elt_id}_main_button",
            position=self.position,
            text=self.value,
            onclick=self.on_main_button_clicked,
            font_name=font_name,
            font_size=font_size
        )
        #
        # 2nd side: the buttons list to select a new option / see all the available options
        #
        self.bts_options_container: ND_Container = ND_Container(
            window=self.window,
            elt_id=f"{self.elt_id}_bts_options_container",
            position=ND_Position(x=self.x, y=self.y, w=self.w, h=self.option_list_buttons_height),
            element_alignment="col",
            scroll_h=True,
            overflow_hidden=True
        )
        self.bts_options_container.visible = False
        #
        option: str
        for option in self.options:
            self.options_bts[option] = ND_Button(
                window=self.window,
                elt_id=f"{self.elt_id}_bt_option_{option}",
                position=ND_Position_Container(w=self.w, h=self.h, container=self.bts_options_container),
                text=option,
                onclick=lambda x, option=option: self.on_option_button_clicked(option), # type: ignore
                font_name=self.font_name,
                font_size=self.font_size
            )
            self.bts_options_container.add_element(self.options_bts[option])

    #
    def render(self) -> None:
        #
        if self.state == "base":
            self.main_button.render()
        else:
            self.bts_options_container.render()

    #
    def update_layout(self) -> None:
        #
        self.bts_options_container.position = ND_Position(x=self.x, y=self.y, w=self.w, h=self.option_list_buttons_height)
        #
        self.bts_options_container.update_layout()

    #
    def add_option(self, option_value: str) -> None:
        #
        if option_value in self.options:
            return
        #
        self.options.add(option_value)

        #
        self.options_bts[option_value] = ND_Button(
            window=self.window,
            elt_id=f"{self.elt_id}_bt_option_{option_value}",
            position=ND_Position_Container(w=self.w, h=self.h, container=self.bts_options_container),
            text=option_value,
            onclick=lambda x, option=option_value: self.on_option_button_clicked(option), # type: ignore
            font_name=self.font_name,
            font_size=self.font_size
        )
        self.bts_options_container.add_element(self.options_bts[option_value])

        #
        self.update_layout()

    #
    def remove_option(self, option_value: str, new_value: Optional[str] = None) -> None:
        #
        if option_value not in self.options:
            return
        #
        if len(self.options) == 1:  # On ne veut pas ne plus avoir d'options possibles
            return
        #
        self.bts_options_container.remove_element(self.options_bts[option_value])
        #
        del self.options_bts[option_value]
        self.options.remove(option_value)
        #
        if self.value == option_value:
            #
            if new_value is not None and new_value in self.options:
                self.value = new_value
            #
            else:
                #
                self.value = next(iter(self.options))
            #
            self.main_button.text = self.value
        #
        self.update_layout()

    #
    def update_options(self, new_options: set[str], new_value: Optional[str] = None) -> None:
        #
        if len(new_options) == 0:
            return
        #
        for bt in self.options_bts.values():
            self.bts_options_container.remove_element(bt)
        #
        self.options_bts = {}
        #
        self.options = new_options
        #
        option: str
        for option in self.options:
            self.options_bts[option] = ND_Button(
                window=self.window,
                elt_id=f"{self.elt_id}_bt_option_{option}",
                position=ND_Position_Container(w=self.w, h=self.h, container=self.bts_options_container),
                text=option,
                onclick=lambda x, option=option: self.on_option_button_clicked(option), # type: ignore
                font_name=self.font_name,
                font_size=self.font_size
            )
            self.bts_options_container.add_element(self.options_bts[option])

        #
        if self.value not in self.options:
            #
            if new_value is not None and new_value in self.options:
                self.value = new_value
            #
            else:
                #
                self.value = next(iter(self.options))
            #
            self.main_button.text = self.value
        #
        self.update_layout()

    #
    def set_state_base(self) -> None:
        #
        self.state = "base"
        self.bts_options_container.visible = False
        self.main_button.visible = True

    #
    def set_state_selection(self) -> None:
        #
        self.state = "selection"
        #
        self.bts_options_container.visible = True
        self.main_button.visible = False

    #
    def handle_event(self, event: nd_event.ND_Event) -> None:
        #
        if event.blocked:
            return
        #
        if self.state == "base":
            self.main_button.handle_event(event)
        else:
            self.bts_options_container.handle_event(event)
            #
            if isinstance(event, nd_event.ND_EventMouseButtonDown):
                if not self.bts_options_container.position.rect.contains_point(ND_Point(event.x, event.y)):
                    self.set_state_base()

    #
    def on_main_button_clicked(self, _) -> None:
        #
        self.set_state_selection()

    #
    def on_option_button_clicked(self, new_option: str) -> None:
        #
        self.value = new_option
        self.main_button.text = self.value
        #
        self.set_state_base()
        #
        if self.on_value_selected is not None:
            self.on_value_selected(self, self.value)


# ND_Container class implementation
class ND_Container(ND_Elt):
    #
    def __init__(
            self,
            window: ND_Window,
            elt_id: str,
            position: ND_Position,
            overflow_hidden: bool = True,
            scroll_w: bool = False,
            scroll_h: bool = False,
            element_alignment: str = "row_wrap",
            element_alignment_kargs: dict[str, int | float | str | bool] = {},
            inverse_z_order: bool = False,
            min_space_width_containing_elements: int = 0,
            min_space_height_containing_elements: int = 0,
            scrollbar_w_height: int = 20,
            scrollbar_h_width: int = 20,
            scroll_speed_w: int = 4,
            scroll_speed_h: int = 4
        ) -> None:

        #
        super().__init__(window=window, elt_id=elt_id, position=position)

        # If the elements overflows are hidden or not (only used in the render() function)
        self.overflow_hidden: bool = overflow_hidden

        # If the container is a scrollable container in theses directions
        self.scroll_w: bool = scroll_w
        self.scroll_h: bool = scroll_h

        #
        self.scroll_speed_w: int = scroll_speed_w
        self.scroll_speed_h: int = scroll_speed_h

        #
        self.scroll_x: float = 0
        self.scroll_y: float = 0
        self.last_scroll_x: float = 0
        self.last_scroll_y: float = 0

        # The current scroll value
        self.scroll: ND_Point = ND_Point(0, 0)

        # If the elements are aligned in a row, a column, a row with wrap, a column with wrap or a grid
        self.element_alignment: str = element_alignment
        self.element_alignment_kargs: dict[str, int | float | str | bool] = element_alignment_kargs
        self.inverse_z_order: bool = inverse_z_order

        # List of contained elements
        self.elements: list[ND_Elt] = []
        #
        self.elements_by_id: dict[str, ND_Elt] = {}

        # Elements that represents the scrollbar if there is one
        self.w_scrollbar: Optional[ND_H_ScrollBar] = None
        self.h_scrollbar: Optional[ND_V_ScrollBar] = None

        #
        self.scrollbar_w_height: int = scrollbar_w_height
        self.scrollbar_h_width: int = scrollbar_h_width

        # Representing the total contained content width and height
        self.content_width: int = 0
        self.content_height: int = 0

        # To help giving contained element space.
        self.min_space_width_containing_elements: int = min_space_width_containing_elements
        self.min_space_height_containing_elements: int = min_space_height_containing_elements

    #
    def update_scroll_layout(self) -> None:
        #
        self.scroll_x = -self.w_scrollbar.scroll_position if self.w_scrollbar else 0
        self.scroll_y = -self.h_scrollbar.scroll_position if self.h_scrollbar else 0
        #
        self.update_layout()
        #
        return
        # #
        # scroll_dx: int = int(self.last_scroll_x - self.scroll_x)
        # scroll_dy: int = int(self.last_scroll_y - self.scroll_y)
        # #
        # elt: ND_Elt
        # for elt in self.elements:
        #     #
        #     elt.position.x += scroll_dx
        #     elt.position.y += scroll_dy
        #     #
        #     if hasattr(elt, "update_scroll_layout"):
        #         elt.update_scroll_layout()
        # #
        # self.last_scroll_x = self.scroll_x
        # self.last_scroll_y = self.scroll_y

    #
    def add_element(self, element: ND_Elt) -> None:
        #
        if element.elt_id in self.elements_by_id:
            raise IndexError(f"Error: Trying to add an element with id {element.elt_id} in container {self.elt_id}, but there was already an element with the same id in there!")
        #
        self.elements.append(element)
        self.elements_by_id[element.elt_id] = element
        #
        self.update_layout()
        #
        if hasattr(element, "update_layout"):
            element.update_layout()

    #
    def remove_element(self, element: ND_Elt) -> None:
        #
        if element.elt_id not in self.elements_by_id:
            raise IndexError(f"Error: Trying to remove an element with id {element.elt_id} in container {self.elt_id}, but there aren't such elements in there !")
        #
        self.elements.remove(element)
        del self.elements_by_id[element.elt_id]
        #
        self.update_layout()

    #
    def remove_element_from_elt_id(self, elt_id: str) -> None:
        #
        if elt_id not in self.elements_by_id:
            raise IndexError(f"Error: Trying to remove an element with id {elt_id} in container {self.elt_id}, but there aren't such elements in there !")
        #
        element: ND_Elt = self.elements_by_id[elt_id]
        #
        self.elements.remove(element)
        del self.elements_by_id[element.elt_id]
        #
        self.update_layout()

    #
    def update_layout(self) -> None:
        #
        if self.element_alignment == "row_wrap":
            self._layout_row_wrap()
        elif self.element_alignment == "col_wrap":
            self._layout_column_wrap()
        elif self.element_alignment == "grid":
            self._layout_grid()
        elif self.element_alignment == "col":
            self._layout_column()
        else:  #  self.element_alignment == "row"
            self._layout_row()

        #
        for elt in self.elements:
            if hasattr(elt, "update_layout"):
                elt.update_layout()

        #
        if self.scroll_w:
            #
            if self.content_width > self.w:
                #
                if not self.w_scrollbar:
                    self.w_scrollbar = ND_H_ScrollBar(
                                                        window=self.window,
                                                        elt_id=f"{self.elt_id}_wscroll",
                                                        position=ND_Position(self.x, self.y + self.h - self.scrollbar_w_height, self.w, self.scrollbar_w_height),
                                                        content_width=self.content_width,
                                                        on_value_changed=lambda elt, value: self.update_scroll_layout()
                    )
                #
                else:
                    self.w_scrollbar.content_width = self.content_width
                    self.w_scrollbar.position.set_x(self.x)
                    self.w_scrollbar.position.set_y(self.y + self.h - self.scrollbar_w_height)
                    self.w_scrollbar.position.set_w(self.w)
                    self.w_scrollbar.position.set_h(self.scrollbar_w_height)
            #
            elif self.w_scrollbar:
                #
                del(self.w_scrollbar)
                self.w_scrollbar = None

        #
        if self.scroll_h:
            #
            if self.content_height > self.h:
                #
                if not self.h_scrollbar:
                    self.h_scrollbar = ND_V_ScrollBar(
                                                        window=self.window,
                                                        elt_id=f"{self.elt_id}_hscroll",
                                                        position=ND_Position(self.x + self.w - self.scrollbar_h_width, self.y, self.scrollbar_h_width, self.h),
                                                        content_height=self.content_height,
                                                        on_value_changed=lambda elt, value: self.update_scroll_layout()
                    )
                #
                else:
                    self.h_scrollbar.content_height = self.content_height
                    self.h_scrollbar.position.set_x(self.x + self.w - self.scrollbar_h_width)
                    self.h_scrollbar.position.set_y(self.y)
                    self.h_scrollbar.position.set_w(self.scrollbar_h_width)
                    self.h_scrollbar.position.set_h(self.h)
            #
            elif self.h_scrollbar:
                #
                del(self.h_scrollbar)
                self.h_scrollbar = None

    #
    def _layout_row_wrap(self) -> None:
        # Initialize row tracking variables
        rows_height: list[int] = [0]
        rows_width: list[int] = [0]
        rows_left_width_total_weight: list[float] = [0]
        rows: list[list[ND_Elt]] = [ [] ]

        #
        crt_x: int = 0
        max_x: int = self.w

        # First pass
        for elt in self.elements:
            #
            elt_w: int = max(elt.w, self.min_space_width_containing_elements) + elt.get_margin_left() + elt.get_margin_right()
            elt_h: int = max(elt.h, self.min_space_height_containing_elements) + elt.get_margin_top() + elt.get_margin_bottom()
            elt_stretch_ratio: float = elt.get_width_stretch_ratio()

            # Si ca dépasse, on crée une nouvelle ligne
            if rows_width[-1] + elt_w >= max_x:
                #
                rows_height.append(elt_h)
                rows_width.append(elt_w)
                rows_left_width_total_weight.append(elt_stretch_ratio)
                rows.append([elt])
                #
                continue

            # Sinon, on ajoute à la ligne actuelle
            #
            rows_height[-1] = max( rows_height[-1], elt_h )
            rows_width[-1] = rows_width[-1] + elt_w
            rows_left_width_total_weight[-1] += elt_stretch_ratio
            rows[-1].append( elt )

        #
        self.content_height = sum(rows_height)
        self.content_width = max(rows_width)
        #
        self.last_scroll_y = self.scroll_y
        self.last_scroll_x = self.scroll_x
        crt_y: int = self.y + int(self.scroll_y)
        space_left: int = 0

        # Second pass
        for i_row in range(len(rows)):
            #
            crt_x = self.x + int(self.scroll_x)
            space_left = self.w - rows_width[i_row]
            #
            for elt in rows[i_row]:
                #
                margin_left: int = 0
                margin_right: int = 0
                margin_top: int = 0
                elt_space_left: int = 0
                #
                if isinstance(elt.position, ND_Position_Container):
                    #
                    elt_stretch_ratio = elt.position.get_width_stretch_ratio()
                    #
                    if elt_stretch_ratio > 0:
                        # We can assume that if elt_stretch_ratio is > 0, the rows_left_width_total_weight[i_row] is > 0
                        elt_space_left = int( float(space_left) * (elt_stretch_ratio / rows_left_width_total_weight[i_row] ) )
                    #
                    margin_left = elt.get_margin_left(elt_space_left)
                    margin_right = elt.get_margin_right(elt_space_left)
                    margin_top = elt.get_margin_top(rows_height[i_row] - elt.h)
                #
                elt.position.set_x(crt_x + margin_left)
                crt_x += elt.w + margin_left + margin_right
                elt.position.set_y(crt_y + margin_top)
            #
            crt_y += rows_height[i_row]

    #
    def _layout_row(self) -> None:

        # Initialize row tracking variables
        row_width: int = 0
        row_left_width_total_weight: float = 0

        #
        crt_x: int = 0

        # First pass
        for elt in self.elements:
            #
            elt_w: int = max(elt.w, self.min_space_width_containing_elements) + elt.get_margin_left() + elt.get_margin_right()
            elt_stretch_ratio: float = elt.get_width_stretch_ratio()

            # On ajoute à la ligne actuelle
            row_width = row_width + elt_w
            row_left_width_total_weight += elt_stretch_ratio

        ##
        self.content_width = row_width
        #
        if isinstance(self.position, ND_Position_Container) and self.position.is_w_auto():
            self.position._w = self.content_width
        #
        self.last_scroll_y = self.scroll_y
        crt_y: int = self.y + int(self.scroll_y)
        space_left: int = 0

        # Second pass
        #
        self.content_height = 0
        #
        self.last_scroll_x = self.scroll_x
        crt_x = self.x + int(self.scroll_x)
        space_left = self.w - row_width
        #
        for elt in self.elements:
            #
            margin_left: int = 0
            margin_right: int = 0
            margin_top: int = 0
            margin_bottom: int = 0
            elt_space_left: int = 0
            #
            if isinstance(elt.position, ND_Position_Container):
                #
                elt_stretch_ratio = elt.position.get_width_stretch_ratio()
                #
                if elt_stretch_ratio > 0:
                    # We can assume that if elt_stretch_ratio is > 0, the rows_left_width_total_weight[i_row] is > 0
                    elt_space_left = int( float(space_left) * (elt_stretch_ratio / row_left_width_total_weight ) )
                #
                margin_left = elt.get_margin_left(elt_space_left)
                margin_right = elt.get_margin_right(elt_space_left)
                margin_top = elt.get_margin_top(self.h - elt.h)
                margin_bottom = elt.get_margin_bottom(self.h - elt.h)
            #
            elt.position.set_x(crt_x + margin_left)
            crt_x += elt.w + margin_left + margin_right
            elt.position.set_y(crt_y + margin_top)
            #
            if margin_top + elt.h + margin_bottom > self.content_height:
                self.content_height = margin_top + elt.h + margin_bottom

    #
    def _layout_column_wrap(self) -> None:

        # Initialize col tracking variables
        cols_height: list[int] = [0]
        cols_width: list[int] = [0]
        cols_left_height_total_weight: list[float] = [0]
        cols: list[list[ND_Elt]] = [ [] ]

        #
        crt_y: int = 0
        max_y: int = self.h

        # First pass
        for elt in self.elements:
            #
            elt_w: int = max(elt.w, self.min_space_width_containing_elements) + elt.get_margin_left() + elt.get_margin_right()
            elt_h: int = max(elt.h, self.min_space_height_containing_elements) + elt.get_margin_top() + elt.get_margin_bottom()
            elt_stretch_ratio: float = elt.get_height_stretch_ratio()

            # Si ca dépasse, on crée une nouvelle ligne
            if cols_height[-1] + elt_h > max_y:
                #
                cols_height.append(elt_h)
                cols_width.append(elt_w)
                cols_left_height_total_weight.append(elt_stretch_ratio)
                cols.append([elt])
                #
                continue

            # Sinon, on ajoute à la ligne actuelle
            #
            cols_width[-1] = max( cols_width[-1], elt_w )
            cols_height[-1] = cols_height[-1] + elt_h
            cols_left_height_total_weight[-1] += elt_stretch_ratio
            cols[-1].append( elt )

        #
        self.content_height = max(cols_height)
        self.content_width = sum(cols_width)
        #
        self.last_scroll_x = self.scroll_x
        self.last_scroll_y = self.scroll_y
        crt_x: int = self.x + int(self.scroll_x)
        space_left: int = 0

        # Second pass
        for i_col in range(len(cols)):
            #
            crt_y = self.y + int(self.scroll_y)
            space_left = self.h - cols_height[i_col]
            #
            for elt in cols[i_col]:
                #
                margin_top: int = 0
                margin_bottom: int = 0
                margin_left: int = 0
                elt_space_left: int = 0
                #
                if isinstance(elt.position, ND_Position_Container):
                    #
                    elt_stretch_ratio = elt.position.get_width_stretch_ratio()
                    #
                    if elt_stretch_ratio > 0:
                        # We can assume that if elt_stretch_ratio is > 0, the cols_left_height_total_weight[i_col] is > 0
                        elt_space_left = int( float(space_left) * (elt_stretch_ratio / cols_left_height_total_weight[i_col] ) )
                    #
                    margin_top = elt.get_margin_top(elt_space_left)
                    margin_bottom = elt.get_margin_bottom(elt_space_left)
                    margin_left = elt.get_margin_top(cols_width[i_col] - elt.w)
                #
                elt.position.set_x(crt_x + margin_left)
                elt.position.set_y(crt_y + margin_top)
                crt_y += elt.h + margin_top + margin_bottom
            #
            crt_x += cols_width[i_col]

    #
    def _layout_column(self) -> None:

        # Initialize col tracking variables
        col_height: int = 0
        col_left_height_total_weight: float = 0

        #
        crt_y: int = 0

        # First pass
        for elt in self.elements:
            #
            elt_h: int = max(elt.h, self.min_space_height_containing_elements) + elt.get_margin_top() + elt.get_margin_bottom()
            elt_stretch_ratio: float = elt.get_height_stretch_ratio()

            # Sinon, on ajoute à la ligne actuelle
            #
            col_height = col_height + elt_h
            col_left_height_total_weight += elt_stretch_ratio

        #
        self.last_scroll_x = self.scroll_x
        crt_x: int = self.x + int(self.scroll_x)
        space_left: int = 0


        ##
        self.content_height = col_height
        #
        if isinstance(self.position, ND_Position_Container) and self.position.is_h_auto():
            self.position._h = col_height

        # Second pass
        #
        self.content_width = 0
        #
        self.last_scroll_y = self.scroll_y
        crt_y = self.y + int(self.scroll_y)
        space_left = self.h - col_height
        #
        for elt in self.elements:
            #
            margin_top: int = 0
            margin_bottom: int = 0
            margin_left: int = 0
            margin_right: int = 0
            elt_space_left: int = 0
            #
            if isinstance(elt.position, ND_Position_Container):
                #
                elt_stretch_ratio = elt.position.get_width_stretch_ratio()
                #
                if elt_stretch_ratio > 0 and col_left_height_total_weight > 0:
                    # We can assume that if elt_stretch_ratio is > 0, the col_left_height_total_weight is > 0
                    elt_space_left = int( float(space_left) * (elt_stretch_ratio / col_left_height_total_weight ) )
                #
                margin_top = elt.get_margin_top(elt_space_left)
                margin_bottom = elt.get_margin_bottom(elt_space_left)
                margin_left = elt.get_margin_left(self.w - elt.w)
                margin_right = elt.get_margin_right(self.w - elt.w)
            #
            elt.position.set_x(crt_x + margin_left)
            elt.position.set_y(crt_y + margin_top)
            crt_y += elt.h + margin_top + margin_bottom
            #
            if margin_left + elt.w + margin_right > self.content_width:
                self.content_width = margin_left + elt.w + margin_right
        #
        self.content_height = crt_y

    #
    def _layout_grid(self):
        #
        cols = self.element_alignment_kargs.get("cols", 3)
        row_spacing = self.element_alignment_kargs.get("row_spacing", 5)
        col_spacing = self.element_alignment_kargs.get("col_spacing", 5)

        max_width = (self.w - (cols - 1) * col_spacing) // cols
        x, y = 0, 0
        row_height = 0

        #
        self.last_scroll_x = self.scroll_x
        self.last_scroll_y = self.scroll_y

        #
        for i, element in enumerate(self.elements):
            element.position._w = min(element.w, max_width)
            if i % cols == 0 and i != 0:
                x = 0
                y += row_height + row_spacing
                row_height = 0
            element._x = self.x + int(self.scroll_x) + x
            element._y = self.y + int(self.scroll_y) + y
            x += element.tx + col_spacing
            row_height = max(row_height, element.ty)

        self.content_width = self.w
        self.content_height = y + row_height

    #
    def render(self) -> None:
        #
        if not self.visible:
            return

        #
        if self.overflow_hidden:
            self.window.enable_area_drawing_constraints(self.x, self.y, self.w, self.h)

        # Render each element with the scrollbar offsets applied
        elt: ND_Elt
        rendering_order = range(len(self.elements))
        #
        if self.inverse_z_order:
            rendering_order = rendering_order[::-1]
        #
        for i in rendering_order:
            #
            elt = self.elements[i]

            #
            elt.render()


        # Remove clipping
        if self.overflow_hidden:
            self.window.disable_area_drawing_constraints()

        # Render scrollbars
        if self.w_scrollbar:
            self.w_scrollbar.render()
        if self.h_scrollbar:
            self.h_scrollbar.render()

    #
    def handle_event(self, event: nd_event.ND_Event) -> None:
        #
        if event.blocked:
            return
        #
        if self.w_scrollbar:
            self.w_scrollbar.handle_event(event)
        if self.h_scrollbar:
            self.h_scrollbar.handle_event(event)

        # Mouse scroll events
        if isinstance(event, nd_event.ND_EventMouseWheelScrolled):
            #
            update_scroll: bool = False
            #
            if self.h_scrollbar is not None:
                #
                self.h_scrollbar.scroll_position = clamp(self.h_scrollbar.scroll_position + event.scroll_y * self.scroll_speed_h, 0, self.h_scrollbar.content_height)
                #
                update_scroll = True
            #
            if self.w_scrollbar is not None:
                #
                self.w_scrollbar.scroll_position = clamp(self.w_scrollbar.scroll_position + event.scroll_x * self.scroll_speed_w, 0, self.w_scrollbar.content_width)
                #
                update_scroll = True
            #
            if update_scroll:
                self.update_scroll_layout()


        # Propagate events to child elements
        elt_order = range(len(self.elements))
        #
        if not self.inverse_z_order:
            elt_order = elt_order[::-1]
        #
        for i in elt_order:
            #
            element = self.elements[i]
            if hasattr(element, 'handle_event'):
                element.handle_event(event)


# ND_MultiLayer class implementation
class ND_MultiLayer(ND_Elt):
    #
    def __init__(
                    self,
                    window: ND_Window,
                    elt_id: str,
                    position: ND_Position,
                    elements_layers: dict[int, ND_Elt] = {}
    ) -> None:

        #
        super().__init__(window=window, elt_id=elt_id, position=position)


        # list of elements sorted by render importance with layers (ascending order)
        self.elements_layers: dict[int, ND_Elt] = elements_layers
        self.elements_by_id: dict[str, ND_Elt] = {}

        #
        layer: int
        elt: ND_Elt
        #
        for layer in self.elements_layers:
            #
            elt = self.elements_layers[layer]
            element_id = elt.elt_id
            #
            if element_id in self.elements_by_id:
                raise UserWarning(f"Error: at least two elements have the same id: {element_id}!")
            #
            self.elements_by_id[element_id] = elt
            #
            self.update_layout_of_element(elt)
        #
        self.layers_keys: list[int] = sorted(list(self.elements_layers.keys()))

    #
    def handle_event(self, event) -> None:
        #
        if event.blocked:
            return
        #
        for elt in self.elements_by_id.values():

            #
            if hasattr(elt, "handle_event"):
                elt.handle_event(event)

        # TODO: gérer les évenenements en fonctions de si un layer du dessus bloque les évenements en dessous

        # #
        # layer: int
        # for layer in self.layers_keys[::-1]:

        #     elt_list: list[str] = self.collisions_layers[layer].get_colliding_ids( (event.button.x, event.button.y) )

        #     for elt_id in elt_list:
        #         self.elements_by_id[elt_id].handle_event(event)

        #     if len(elt_list) > 0:
        #         return

    #
    def update_layout_of_element(self, elt: ND_Elt) -> None:
        #
        ew: int = elt.w
        eh: int = elt.h
        emt: int = elt.get_margin_top(self.h - eh)
        eml: int = elt.get_margin_left(self.w - ew)
        #
        enx: int = self.x + eml
        eny: int = self.y + emt
        #
        elt.position.set_x(enx)
        elt.position.set_y(eny)
        #
        if hasattr(elt, "update_layout"):
            elt.update_layout()

    #
    def update_layout(self) -> None:
        #
        for elt in self.elements_by_id.values():
            #
            self.update_layout_of_element(elt)

    #
    def insert_to_layers_keys(self, layer_key: int) -> None:

        if ( len(self.layers_keys) == 0 ) or ( layer_key > self.layers_keys[-1] ):
            self.layers_keys.append(layer_key)
            return

        # Insertion inside a sorted list by ascendant
        i: int
        k: int
        for i, k in enumerate(self.layers_keys):
            if k > layer_key:
                self.layers_keys.insert(i, layer_key)
                return

    #
    def add_element(self, layer_id: int, elt: ND_Elt) -> None:
        #
        elt_id: str = elt.elt_id

        #
        if elt_id in self.elements_by_id:
            raise UserWarning(f"Error: at least two elements in the multi-layer {self.elt_id} have the same id: {elt_id}!")

        #
        if layer_id not in self.elements_layers:
            self.elements_layers[layer_id] = elt
            self.elements_by_id[elt.elt_id] = elt
            self.insert_to_layers_keys(layer_id)
            #
            self.update_layout_of_element(elt)
        #
        else:
            raise UserWarning(f"Error: trying to insert an element to multi-layer {self.elt_id} on the same layer than another element!")

    #
    def render(self) -> None:
        #
        layer_key: int
        for layer_key in self.layers_keys:
            #
            element: ND_Elt = self.elements_layers[layer_key]
            #
            element.render()


#
class ND_CameraScene(ND_Elt):
    #
    def __init__(self, window: ND_Window, elt_id: str, position: ND_Position, scene_to_render: ND_Scene, zoom: float = 1.0) -> None:
        #
        super().__init__(window=window, elt_id=elt_id, position=position)
        #
        self.scene_to_render: ND_Scene = scene_to_render
        self.zoom: float = zoom

    #
    def render(self) -> None:
        # TODO
        pass


#
class ND_CameraGrid(ND_Elt):
    #
    def __init__(self, window: ND_Window, elt_id: str, position: ND_Position, grids_to_render: list["ND_RectGrid"], zoom_x: float = 1.0, zoom_y: float = 1.0) -> None:
        #
        super().__init__(window=window, elt_id=elt_id, position=position)
        #
        self.grids_to_render: list[ND_RectGrid] = grids_to_render
        #
        self.origin: ND_Point = ND_Point(0, 0)
        self.zoom_x: float = zoom_x
        self.zoom_y: float = zoom_y
        #
        self.min_zoom: float = 0.1
        self.max_zoom: float = 100
        #
        self.grid_lines_width: int = 0
        self.grid_lines_color: ND_Color = ND_Color(255, 255, 255)
        grid_to_render: ND_RectGrid
        for grid_to_render in self.grids_to_render:
            if grid_to_render.grid_lines_width > self.grid_lines_width:
                self.grid_lines_width = grid_to_render.grid_lines_width
                self.grid_lines_color = grid_to_render.grid_lines_color

    #
    def render(self) -> None:
        #
        if len(self.grids_to_render) == 0:  # If no grids to render
            return
        #
        zx: float = clamp(self.zoom_x, self.min_zoom, self.max_zoom)
        zy: float = clamp(self.zoom_y, self.min_zoom, self.max_zoom)
        #
        self.window.enable_area_drawing_constraints(self.x, self.y, self.w, self.h)
        #
        gtx: int = int(zx * self.grids_to_render[0].grid_tx)
        gty: int = int(zy * self.grids_to_render[0].grid_ty)
        #
        lines_width: int = 0
        if self.grid_lines_width > 0:
            lines_width = max( 1, round( max(zx, zy) * self.grid_lines_width ) )
        #
        deb_x: int = self.origin.x # math.ceil( self.origin.x / (gtx + lines_width) )
        deb_y: int = self.origin.y # math.ceil( self.origin.y / (gty + lines_width) )
        fin_x: int = self.origin.x + math.ceil( (self.w) / (gtx) ) + 1
        fin_y: int = self.origin.y + math.ceil( (self.h) / (gty) ) + 1

        # Dessin des lignes
        cx: int
        cy: int
        dcx: int
        dcy: int
        for cx in range(deb_x, fin_x + 1):
            #
            dcx = self.x + int((cx-deb_x) * gtx)

            # Dessin ligne
            self.window.draw_thick_line(
                                            x1=dcx, x2=dcx, y1=self.y, y2=self.y+self.h,
                                            color=self.grid_lines_color,
                                            line_thickness=lines_width
            )

        #
        for cy in range(deb_y, fin_y + 1):
            #
            dcy = self.y + int((cy-deb_y) * gty)

            # Dessin Ligne
            self.window.draw_thick_line(
                                            x1=self.x, x2=self.x+self.w, y1=dcy, y2=dcy,
                                            color=self.grid_lines_color,
                                            line_thickness=lines_width
            )

        #
        grid_to_render: ND_RectGrid
        for grid_to_render in self.grids_to_render:

            # Dessin des éléments
            for cx in range(deb_x, fin_x + 1):
                #
                dcx = self.x + int((cx-deb_x) * gtx)
                #
                for cy in range(deb_y, fin_y + 1):
                    #
                    dcy = self.y + int((cy-deb_y) * gty)
                    #
                    elt: Optional[ND_Elt] = grid_to_render.get_element_at_grid_case(ND_Point(cx, cy))
                    #
                    if elt is None:
                        continue
                    #
                    old_position: ND_Position = elt.position
                    if hasattr(elt, "transformations"):
                        old_transformations: ND_Transformations = elt.transformations
                        #
                        if ND_Point(cx, cy) in grid_to_render.grid_transformations:
                            elt.transformations = elt.transformations + grid_to_render.grid_transformations[ND_Point(cx, cy)]
                    #
                    elt.position = ND_Position(dcx, dcy, int(gtx), int(gty))
                    #
                    elt.render()
                    #
                    elt.position = old_position
                    #
                    if hasattr(elt, "transformations"):
                        elt.transformations = old_transformations
                    #

        #
        self.window.disable_area_drawing_constraints()
        #

    #
    def move_camera_to_grid_area(self, grid_area: ND_Rect, force_square_tiles: bool = True) -> None:
        #
        if not self.grids_to_render:
            return
        #
        self.origin.x = grid_area.x - 1
        self.origin.y = grid_area.y - 1
        #
        self.zoom_x = float(self.w) / float((grid_area.w+3) * (self.grids_to_render[0].grid_tx+self.grid_lines_width))
        self.zoom_y = float(self.h) / float((grid_area.h+3) * (self.grids_to_render[0].grid_ty+self.grid_lines_width))
        #
        if force_square_tiles:
            mz: float = min(self.zoom_x, self.zoom_y)
            self.zoom_x = mz
            self.zoom_y = mz


#
class ND_RectGrid(ND_Elt):
    #
    def __init__(self, window: ND_Window, elt_id: str, position: ND_Position, grid_tx: int, grid_ty: int, grid_lines_width: int = 0, grid_lines_color: ND_Color = ND_Color(0, 0, 0)) -> None:
        #
        super().__init__(window=window, elt_id=elt_id, position=position)
        #
        self.default_element_grid_id: int = -1  # elt_grid_id < 0 => is None, Nothing is displayed
        #
        self.grid_tx: int = grid_tx
        self.grid_ty: int = grid_ty
        #
        self.grid_lines_width: int = grid_lines_width
        self.grid_lines_color: ND_Color = grid_lines_color
        #
        self.grid_elements_by_id: dict[int, ND_Elt] = {}
        self.grid_positions_by_id: dict[int, set[ND_Point]] = {}
        self.elements_to_grid_id: dict[ND_Elt, int] = {}  # hash = object's pointer / (general/memory) id
        #
        self.next_available_id: int = 0
        #
        self.grid: dict[ND_Point, int] = {}  # dict key = (ND_Point=hash(f"{x}_{y}")) -> elt_grid_id
        self.grid_transformations: dict[ND_Point, ND_Transformations] = {}

    # Supprime tout, grille, éléments, ...
    def clean(self) -> None:
        #
        self.default_elt_grid_id = -1
        #
        self.grid_elements_by_id = {}
        self.grid_positions_by_id = {}
        self.elements_to_grid_id = {}
        #
        self.next_available_id = 0
        #
        self.grid = {}

    #
    def _set_grid_position(self, position: ND_Point, elt_grid_id: int = -1) -> None:
        #
        if elt_grid_id >= 0:
            self.grid[position] = elt_grid_id
            self.grid_positions_by_id[elt_grid_id].add(position)  # On ajoute la position de l'élement
        #
        elif position in self.grid:
            #
            old_elt_grid_id: int = self.grid[position]
            if old_elt_grid_id in self.grid_positions_by_id:  # On supprime la position de l'ancien element
                #
                if position in self.grid_positions_by_id[old_elt_grid_id]:
                    self.grid_positions_by_id[old_elt_grid_id].remove(position)
            #
            del self.grid[position]

    #
    def add_element_to_grid(self, element: ND_Elt, position: ND_Point | list[ND_Point]) -> int:
        #
        if element not in self.elements_to_grid_id:
            self.elements_to_grid_id[element] = self.next_available_id
            self.grid_elements_by_id[self.next_available_id] = element
            self.grid_positions_by_id[self.next_available_id] = set()
            self.next_available_id += 1
        #
        elt_grid_id = self.elements_to_grid_id[element]
        #
        self.add_element_position(elt_grid_id, position)
        #
        return elt_grid_id

    #
    def add_element_position(self, elt_id: int, position: ND_Point | list[ND_Point]) -> None:
        #
        if isinstance(position, list):  # liste de points
            #
            for pos in position:
                self._set_grid_position(pos, elt_id)
        #
        else:  # Point unique
            self._set_grid_position(position, elt_id)

    #
    def set_transformations_to_position(self, position: ND_Point, transformations: Optional[ND_Transformations]) -> None:
        #
        if transformations is None:
            if position in self.grid_transformations:
                del self.grid_transformations[position]
            return
        #
        self.grid_transformations[position] = transformations

    #
    def remove_element_of_grid(self, element: ND_Elt) -> None:
        #
        if element not in self.elements_to_grid_id:
            return
        #
        elt_id: int = self.elements_to_grid_id[element]

        # On va supprimer toutes les cases de la grille où l'élément était
        position: ND_Point
        for position in self.grid_positions_by_id[elt_id]:
            #
            self._set_grid_position(position, -1)

        # Si l'élément était l'élément par défaut
        if self.default_elt_grid_id == elt_id:
            #
            self.default_elt_grid_id = -1

        #
        del self.grid_positions_by_id[elt_id]
        del self.grid_elements_by_id[elt_id]
        del self.elements_to_grid_id[element]

    #
    def remove_at_position(self, pos: ND_Point) -> None:
        #
        if pos not in self.grid:
            return
        #
        elt_id: int = self.grid[pos]

        #
        if elt_id < 0:
            return

        # On supprimer la position de l'élément
        self.grid_positions_by_id[elt_id].remove(pos)
        self._set_grid_position(pos, -1)

    #
    def get_element_at_grid_case(self, case: ND_Point) -> Optional[ND_Elt]:
        #
        if case not in self.grid:
            return None
        #
        grid_elt_id: int = self.grid[case]
        #
        if grid_elt_id not in self.grid_elements_by_id:
            return None
        #
        return self.grid_elements_by_id[grid_elt_id]

    #
    def get_element_id_at_grid_case(self, case: ND_Point) -> Optional[int]:
        #
        if case not in self.grid:
            return None
        #
        return self.grid[case]

    #
    def get_empty_case_in_range(self, x_min: int, x_max: int, y_min: int, y_max: int) -> Optional[ND_Point]:
        #
        if x_min > x_max or y_min > y_max:
            #
            return None
        #
        dx: int = x_max - x_min
        dy: int = y_max - y_min
        r: int = int(math.sqrt(dx**2 + dy**2))

        # randoms
        xx: int
        yy: int
        p: ND_Point
        for _ in range(0, r):
            #
            xx = random.randint(x_min, x_max)
            yy = random.randint(y_min, y_max)
            p = ND_Point(xx, yy)
            #
            if p not in self.grid:
                return p

        # Brute si le random n'a rien trouvé
        for xx in range(x_min, x_max+1):
            for yy in range(y_min, y_max+1):
                #
                p = ND_Point(xx, yy)
                #
                if p not in self.grid:
                    return p

        #
        return None

    #
    def render(self) -> None:
        # Do nothing here, because it is a camera that have to render
        return

    #
    def export_chunk_of_grid_to_numpy(self, x_0: int, y_0: int, x_1: int, y_1: int, fn_elt_to_value: Callable[[Optional[ND_Elt], Optional[int]], int | float], np_type: type = np.float32) -> np.ndarray:
        #
        dtx: int = x_1 - x_0
        dty: int = y_1 - y_0
        #
        grid: np.ndarray = np.zeros((dtx, dty), dtype=np_type)
        #
        for dx in range(dtx):
            for dy in range(dty):
                #
                case_point: ND_Point = ND_Point(x_0 + dx, y_0 + dy)
                #
                elt: Optional[ND_Elt] = self.get_element_at_grid_case(case_point)
                elt_id: Optional[int] = self.get_element_id_at_grid_case(case_point)
                #
                grid[dx, dy] = fn_elt_to_value(elt, elt_id)
        #
        return grid


#
class ND_Position_RectGrid(ND_Position):
    #
    def __init__(self, rect_grid: ND_RectGrid) -> None:
        #
        super().__init__()
        #
        self.rect_grid: ND_RectGrid = rect_grid
        #

    #
    @property
    def w(self) -> int:
        return self.rect_grid.grid_tx

    #
    @w.setter
    def w(self, new_value: int) -> None:
        # TODO
        pass

    #
    @property
    def h(self) -> int:
        return self.rect_grid.grid_ty

    #
    @h.setter
    def h(self, new_value: int) -> None:
        # TODO
        pass

    #
    def current_grid_case(self, case: ND_Point) -> None:
        self._x = case.x
        self._y = case.y


#
class ND_Position_FullWindow(ND_Position):
    #
    def __init__(self, window: ND_Window) -> None:
        #
        super().__init__()
        #
        self.window = window

    #
    @property
    def x(self) -> int:
        return 0

    #
    @x.setter
    def x(self, new_value: int) -> None:
        # TODO
        pass

    #
    @property
    def y(self) -> int:
        return 0

    #
    @y.setter
    def y(self, new_value: int) -> None:
        # TODO
        pass

    #
    @property
    def w(self) -> int:
        return self.window.width

    #
    @w.setter
    def w(self, new_value: int) -> None:
        # TODO
        pass

    #
    @property
    def h(self) -> int:
        return self.window.height

    #
    @h.setter
    def h(self, new_value: int) -> None:
        # TODO
        pass


#
class ND_Position_Container(ND_Position):
    #
    def __init__(
                    self,
                    w: int | str,
                    h: int | str,
                    container: ND_Container,
                    position_constraints: Optional[ND_Position_Constraints] = None,
                    position_margins: Optional[ND_Position_Margins] = None
    ) -> None:

        #
        self.w_str: Optional[str] = None
        self.h_str: Optional[str] = None

        #
        if isinstance(w, str):
            self.w_str = w
            w = -1

        #
        if isinstance(h, str):
            self.h_str = h
            h = -1

        #
        if self.w_str == "square" and self.h_str == "square":
            raise UserWarning("Error: width and height cannot have attribute 'square' !!!")

        #
        super().__init__(0, 0, w, h)

        #
        self.container: ND_Container = container
        #
        self.positions_constraints: Optional[ND_Position_Constraints] = position_constraints
        self.position_margins: Optional[ND_Position_Margins] = position_margins

    #
    def is_w_auto(self) -> bool:
        return self.w_str == "auto"

    #
    def is_h_auto(self) -> bool:
        return self.h_str == "auto"

    #
    @property
    def w(self) -> int:
        #
        if self.w_str is None:
            return self._w
        #
        elif self.w_str == "auto":
            return max(self._w, 0)
        #
        elif self.w_str == "square":
            return self.h
        #
        w: float = get_percentage_from_str(self.w_str) / 100.0
        #
        width: int = int(w * self.container.w)
        #
        if self.positions_constraints:
            #
            if self.positions_constraints.min_width and width < self.positions_constraints.min_width:
                width = self.positions_constraints.min_width
            #
            if self.positions_constraints.max_width and width > self.positions_constraints.max_width:
                width = self.positions_constraints.max_width
        #
        return width

    #
    @w.setter
    def w(self, new_value: int) -> None:
        # TODO
        pass

    #
    @property
    def h(self) -> int:
        #
        if self.h_str is None:
            return self._h
        #
        elif self.h_str == "auto":
            return max(self._h, 0)
        #
        elif self.h_str == "square":
            return self.w
        #
        h: float = get_percentage_from_str(self.h_str) / 100.0
        #
        height: int = int(h * self.container.h)
        #
        if self.positions_constraints:
            #
            if self.positions_constraints.min_height and height < self.positions_constraints.min_height:
                height = self.positions_constraints.min_height
            #
            if self.positions_constraints.max_height and height > self.positions_constraints.max_height:
                height = self.positions_constraints.max_height
        #
        return height

    #
    @h.setter
    def h(self, new_value: int) -> None:
        # TODO
        pass

    #
    def get_margin_left(self, space_around: int = -1) -> int:
        #
        if self.position_margins is None:
            return 0

        #
        mleft: Optional[int | str] = self.position_margins.margin_left
        if mleft is None:
            mleft = self.position_margins.margin
        #
        if mleft is None:
            mleft = self.position_margins.min_margin_left

        #
        pleft: float = 0.0

        #
        if isinstance(mleft, int):
            if not isinstance(self.position_margins.margin_right, str):
                return mleft
            #
            pleft = (100.0 - get_percentage_from_str(self.position_margins.margin_right)) / 100.0
        else:
            pleft = get_percentage_from_str(mleft) / 100.0

        #
        return max(
                    self.position_margins.min_margin_left,
                    int( space_around * pleft )
        )

    #
    def get_margin_right(self, space_around: int = -1) -> int:
        #
        if self.position_margins is None:
            return 0

        #
        mval: Optional[int | str] = self.position_margins.margin_right
        if mval is None:
            mval = self.position_margins.margin
        #
        if mval is None:
            mval = self.position_margins.min_margin_right

        #
        pval: float = 0.0

        #
        if isinstance(mval, int):
            if not isinstance(self.position_margins.margin_left, str):
                return mval
            #
            pval = (100.0 - get_percentage_from_str(self.position_margins.margin_left)) / 100.0
        else:
            pval = get_percentage_from_str(mval) / 100.0

        #
        return max(
                    self.position_margins.min_margin_right,
                    int( space_around * pval )
        )

    #
    def get_margin_top(self, space_around: int = -1) -> int:
        #
        if self.position_margins is None:
            return 0

        #
        mval: Optional[int | str] = self.position_margins.margin_top
        if mval is None:
            mval = self.position_margins.margin
        #
        if mval is None:
            mval = self.position_margins.min_margin_top

        #
        pval: float = 0.0

        #
        if isinstance(mval, int):
            if not isinstance(self.position_margins.margin_bottom, str):
                return mval
            #
            pval = (100.0 - get_percentage_from_str(self.position_margins.margin_bottom)) / 100.0
        else:
            pval = get_percentage_from_str(mval) / 100.0

        #
        return max(
                    self.position_margins.min_margin_top,
                    int( space_around * pval )
        )

    #
    def get_margin_bottom(self, space_around: int = -1) -> int:
        #
        if self.position_margins is None:
            return 0

        #
        mval: Optional[int | str] = self.position_margins.margin_bottom
        if mval is None:
            mval = self.position_margins.margin
        #
        if mval is None:
            mval = self.position_margins.min_margin_bottom

        #
        pval: float = 0.0

        #
        if isinstance(mval, int):
            if not isinstance(self.position_margins.margin_top, str):
                return mval
            #
            pval = (100.0 - get_percentage_from_str(self.position_margins.margin_top)) / 100.0
        else:
            pval = get_percentage_from_str(mval) / 100.0

        #
        return max(
                    self.position_margins.min_margin_bottom,
                    int( space_around * pval )
        )

    #
    def get_width_stretch_ratio(self) -> float:
        #
        if self.position_margins is None:
            return 0.0
        #
        if isinstance(self.position_margins.margin_left, str) or isinstance(self.position_margins.margin_right, str):
            return self.position_margins.width_stretch_ratio
        #
        return 0.0

    #
    def get_height_stretch_ratio(self) -> float:
        #
        if self.position_margins is None:
            return 0.0
        #
        if isinstance(self.position_margins.margin_top, str) or isinstance(self.position_margins.margin_bottom, str):
            return self.position_margins.height_stretch_ratio
        #
        return 0.0


#
class ND_Position_MultiLayer(ND_Position):
    #
    def __init__(
                    self,
                    multilayer: ND_MultiLayer,
                    w: int | str = -1,
                    h: int | str = -1,
                    position_constraints: Optional[ND_Position_Constraints] = None,
                    position_margins: Optional[ND_Position_Margins] = None
    ) -> None:

        #
        self.w_str: Optional[str] = None
        self.h_str: Optional[str] = None


        if w is not None and isinstance(w, str):
            self.w_str = w
            w = -1

        #
        if h is not None and isinstance(h, str):
            self.h_str = h
            h = -1

        #
        super().__init__(0, 0, w, h)

        #
        self.multilayer: ND_MultiLayer = multilayer
        #
        self.positions_constraints: Optional[ND_Position_Constraints] = position_constraints
        self.position_margins: Optional[ND_Position_Margins] = position_margins

    #
    @property
    def w(self) -> int:
        #
        if self.w_str is None:
            if self._w <= 0:
                return self.multilayer.w
            #
            return self._w
        #
        w: float = get_percentage_from_str(self.w_str) / 100.0
        #
        return int(w * self.multilayer.w)

    #
    @w.setter
    def w(self, new_value: int) -> None:
        # TODO
        pass

    #
    @property
    def h(self) -> int:
        #
        if self.h_str is None:
            if self._h <= 0:
                return self.multilayer.h
            #
            return self._h
        #
        h: float = get_percentage_from_str(self.h_str) / 100.0
        #
        return int(h * self.multilayer.h)

    #
    @h.setter
    def h(self, new_value: int) -> None:
        # TODO
        pass

    #
    def get_margin_left(self, space_around: int = -1) -> int:
        #
        if self.position_margins is None:
            return 0

        #
        mleft: Optional[int | str] = self.position_margins.margin_left
        if mleft is None:
            mleft = self.position_margins.margin
        #
        if mleft is None:
            mleft = self.position_margins.min_margin_left

        #
        pleft: float = 0.0

        #
        if isinstance(mleft, int):
            if not isinstance(self.position_margins.margin_right, str):
                return mleft
            #
            pleft = (100.0 - get_percentage_from_str(self.position_margins.margin_right)) / 100.0
        else:
            pleft = get_percentage_from_str(mleft) / 100.0

        #
        return max(
                    self.position_margins.min_margin_left,
                    int( space_around * pleft )
        )

    #
    def get_margin_right(self, space_around: int = -1) -> int:
        #
        if self.position_margins is None:
            return 0

        #
        mval: Optional[int | str] = self.position_margins.margin_right
        if mval is None:
            mval = self.position_margins.margin
        #
        if mval is None:
            mval = self.position_margins.min_margin_right

        #
        pval: float = 0.0

        #
        if isinstance(mval, int):
            if not isinstance(self.position_margins.margin_left, str):
                return mval
            #
            pval = (100.0 - get_percentage_from_str(self.position_margins.margin_left)) / 100.0
        else:
            pval = get_percentage_from_str(mval) / 100.0

        #
        return max(
                    self.position_margins.min_margin_right,
                    int( space_around * pval )
        )

    #
    def get_margin_top(self, space_around: int = -1) -> int:
        #
        if self.position_margins is None:
            return 0

        #
        mval: Optional[int | str] = self.position_margins.margin_top
        if mval is None:
            mval = self.position_margins.margin
        #
        if mval is None:
            mval = self.position_margins.min_margin_top

        #
        pval: float = 0.0

        #
        if isinstance(mval, int):
            if not isinstance(self.position_margins.margin_bottom, str):
                return mval
            #
            pval = (100.0 - get_percentage_from_str(self.position_margins.margin_bottom)) / 100.0
        else:
            pval = get_percentage_from_str(mval) / 100.0

        #
        return max(
                    self.position_margins.min_margin_top,
                    int( space_around * pval )
        )

    #
    def get_margin_bottom(self, space_around: int = -1) -> int:
        #
        if self.position_margins is None:
            return 0

        #
        mval: Optional[int | str] = self.position_margins.margin_bottom
        if mval is None:
            mval = self.position_margins.margin
        #
        if mval is None:
            mval = self.position_margins.min_margin_bottom

        #
        pval: float = 0.0

        #
        if isinstance(mval, int):
            if not isinstance(self.position_margins.margin_top, str):
                return mval
            #
            pval = (100.0 - get_percentage_from_str(self.position_margins.margin_top)) / 100.0
        else:
            pval = get_percentage_from_str(mval) / 100.0

        #
        return max(
                    self.position_margins.min_margin_bottom,
                    int( space_around * pval )
        )

    #
    def get_width_stretch_ratio(self) -> float:
        #
        if self.position_margins is None:
            return 0.0
        #
        if isinstance(self.position_margins.margin_left, str) or isinstance(self.position_margins.margin_right, str):
            return self.position_margins.width_stretch_ratio
        #
        return 0.0

    #
    def get_height_stretch_ratio(self) -> float:
        #
        if self.position_margins is None:
            return 0.0
        #
        if isinstance(self.position_margins.margin_top, str) or isinstance(self.position_margins.margin_bottom, str):
            return self.position_margins.height_stretch_ratio
        #
        return 0.0


