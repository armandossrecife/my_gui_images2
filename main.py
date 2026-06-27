import tkinter as tk

import gui


def main():
    main_window = gui.MenuWindow(
        my_app=tk.Tk(),
        my_title="Minhas Imagens",
    )
    main_window.app.mainloop()


if __name__ == "__main__":
    main()
