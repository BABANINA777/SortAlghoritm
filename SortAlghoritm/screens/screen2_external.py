"""Модуль экрана второго практического задания: алгоритмы внешней сортировки."""

import customtkinter as ctk


def create_screen2(parent, on_back):
    """Создает фрейм для внешней сортировки табличных файлов."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")

    # Деление на 3 строки (контейнера)
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)
    frame.grid_rowconfigure(2, weight=1)

    top_frame = ctk.CTkFrame(frame, fg_color="transparent")
    top_frame.grid(row=0, column=0, sticky="nsew")
    content_frame = ctk.CTkFrame(frame, fg_color="transparent")
    content_frame.grid(row=1, column=0, sticky="nsew")
    bottom_frame = ctk.CTkFrame(frame, fg_color="transparent")
    bottom_frame.grid(row=2, column=0, sticky="nsew")

    # Панель управления: кнопка возврата в меню
    btn_back = ctk.CTkButton(
        top_frame,
        command=on_back,
        text="← Назад",
        height=50,
        width=50,
        font=("Arial", 11, "bold"),
        hover_color="#3A3A3A"
    )
    btn_back.grid(row=0, column=0, padx=0, sticky="ew")

    return frame
