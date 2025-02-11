# client.py
import Pyro4
import os
import base64
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class MultimediaClient:
    #* Inicializacion del proxy
    def __init__(self):
        self.server = Pyro4.Proxy("PYRONAME:multimedia.server")
        # se crea una directorio para las descargar si no existe.
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        # se inicializa el gui de tkinter
        self.setup_gui()

    def setup_gui(self):
        """
        Inicializacion de toda la parte grafica requerida para que
        el usuario puede hacer uso de las funciones necesarias que le 
        provee el servidor
        Incluye pestañas, botones, listados, etc.
        """
        self.root = tk.Tk()
        self.root.title("Cliente Multimedia")
        self.root.geometry("600x400")

        # Crear notebook para pestañas
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both')

        # Pestaña de listado y descarga
        download_frame = ttk.Frame(notebook)
        notebook.add(download_frame, text='Ver y Descargar')

        # Lista de archivos
        self.files_tree = ttk.Treeview(download_frame, columns=('ID', 'Nombre', 'Tipo'), show='headings')
        self.files_tree.heading('ID', text='ID')
        self.files_tree.heading('Nombre', text='Nombre')
        self.files_tree.heading('Tipo', text='Tipo')
        self.files_tree.pack(pady=10, padx=10, fill='both', expand=True)

        # Botón de actualizar lista
        ttk.Button(download_frame, text='Actualizar Lista', 
                  command=self.update_file_list).pack(pady=5)

        # Botón de descarga
        ttk.Button(download_frame, text='Descargar Seleccionado', 
                  command=self.download_selected).pack(pady=5)

        # Pestaña de subida
        upload_frame = ttk.Frame(notebook)
        notebook.add(upload_frame, text='Subir Archivo')

        # Botón de seleccionar archivo
        ttk.Button(upload_frame, text='Seleccionar Archivo', 
                  command=self.select_file).pack(pady=20)

        self.selected_file_label = ttk.Label(upload_frame, text='Ningún archivo seleccionado')
        self.selected_file_label.pack(pady=10)

        # Botón de subida
        self.upload_button = ttk.Button(upload_frame, text='Subir Archivo', 
                                      command=self.upload_file, state='disabled')
        self.upload_button.pack(pady=10)

        self.update_file_list()

    def update_file_list(self):
        """
        Funcion relacionada con el boton de actualizacion de tkinter. 
        Permite poder actualizar la lista de multimedia que se muestra en la pestaña. 
        Esto con la finalidad de que si varios usuarios estan realizando subida de archivos
        todos puedan ser capaces de visualizarlo
        
        """
        # Limpiar lista actual
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
            
        # Obtener y mostrar archivos
        files = self.server.list_files()
        for file in files:
            self.files_tree.insert('', 'end', values=(file['id'], file['nombre'], file['tipo']))

    def download_selected(self):
        """
        Funcion relacionada al boton de descargar en tkinter.
        Permite hacer la descarga del archivo que se haya seleccionado. 
        Esta descarga se guardara en la carpeta de downloads que se genera al 
        iniciar el programa del cliente
        """

        selected = self.files_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Por favor seleccione un archivo")
            return

        file_id = int(self.files_tree.item(selected[0])['values'][0])
        file_data, message = self.server.download_file(file_id)
        
        if file_data:
            save_path = self.downloads_dir / file_data['nombre']
            with open(save_path, 'wb') as f:
                f.write(base64.b64decode(file_data['datos']))
            messagebox.showinfo("Éxito", f"Archivo descargado en: {save_path}")
        else:
            messagebox.showerror("Error", message)

    def select_file(self):
        """
        Esta funcion permite que se abra el seleccionador de archivos del usuario
        y que pueda realizar posteriormente la subida de ese archivo.
        Esta funcion actualizaa el valor de file path para poder 
        recuperar los datos que se actualizaran del lado del servidor. 
        
        """
        file_path = filedialog.askopenfilename(
            filetypes=[
                ('Archivos multimedia', 
                 '*.mp3 *.wav *.ogg *.mp4 *.avi *.mkv *.jpg *.jpeg *.png *.gif'),
                ('Todos los archivos', '*.*')
            ]
        )
        if file_path:
            self.selected_file_path = Path(file_path)
            self.selected_file_label.config(text=f'Archivo seleccionado: {self.selected_file_path.name}')
            self.upload_button.config(state='normal')

    def upload_file(self):
        """
        funcion que permite hacer la subida de archivos que ya se haya seleccionado
        desde el manejador de sistemas de archivos del SO del usuario.
        
        """
        try:
            with open(self.selected_file_path, 'rb') as f:
                file_data = base64.b64encode(f.read()).decode('utf-8')
            
            success, message = self.server.upload_file(
                self.selected_file_path.name, 
                file_data
            )
            
            if success:
                messagebox.showinfo("Éxito", message)
                self.update_file_list()
                self.selected_file_label.config(text='Ningún archivo seleccionado')
                self.upload_button.config(state='disabled')
            else:
                messagebox.showerror("Error", message)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al subir archivo: {str(e)}")

    def run(self):
        self.root.mainloop()

def main():
    client = MultimediaClient()
    client.run()

if __name__ == "__main__":
    main()