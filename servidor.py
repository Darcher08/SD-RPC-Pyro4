# server.py
import Pyro4
import os
from pathlib import Path
import base64

@Pyro4.expose
class MultimediaServer:

    def __init__(self):
        #! Creador de directorios
        #* Crear directorio multimedia si no existe
        self.multimedia_dir = Path("multimedia")
        self.multimedia_dir.mkdir(exist_ok=True)
        
        #* Crear subdirectorios para diferentes tipos de archivos
        self.directories = {
            "audio": self.multimedia_dir / "audio",
            "video": self.multimedia_dir / "video",
            "imagen": self.multimedia_dir / "imagen"
        }
        
        # se verifica si no existen lo subdirectorios, si es asi se crean
        for dir_path in self.directories.values():
            dir_path.mkdir(exist_ok=True)

   
    def get_file_type(self, filename):
        """
         Cuando se sube un archivo se verifica que tipo de extension tiene,
        dependiendo de cual se guarda en su direccion correcta.
        """ 

        extension = filename.lower().split('.')[-1]
        if extension in ['mp3', 'wav', 'ogg']:
            return 'audio'
        elif extension in ['mp4', 'avi', 'mkv']:
            return 'video'
        elif extension in ['jpg', 'jpeg', 'png', 'gif']:
            return 'imagen'
        else:
            return None


    def list_files(self):
        """
        Se realiza un listado de todos los archivos disponibles en la 
        carpeta de multimedia para poder mostraselo al usuario. 
        """

        all_files = []
        for dir_type, dir_path in self.directories.items():
            files = list(dir_path.glob('*'))
            all_files.extend([{
                'id': len(all_files) + i + 1,
                'nombre': f.name,
                'tipo': dir_type,
                'ruta': str(f)
            } for i, f in enumerate(files)])
        return all_files

    def upload_file(self, filename, file_data, file_type=None):
        """
        Se verifica que tipo de archivo esta intentando subir el usuario.
        si fuera uno de los permitidos se procede a hacer el agregado al directorio.
        """

        try:
            # Verificar el tipo de archivo
            if file_type is None:
                file_type = self.get_file_type(filename)
                if file_type is None:
                    return False, "Tipo de archivo no soportado"

            # se crea una variable que define la ruta a la cual se va guardar el archivo
            file_path = self.directories[file_type] / filename
            
            # Decodificar datos base64 y escribir archivo
            file_bytes = base64.b64decode(file_data)
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
                
            return True, "Archivo subido exitosamente"
        except Exception as e:
            return False, f"Error al subir archivo: {str(e)}"

    def download_file(self, file_id):

        """
        Si el usuario ha seleccionado un archivo en particular el 
        servidor recibira el id del archivo para poder proporcionarlo.
        """
        try:
            # listar todos los archivos del directorio multimedia
            files = self.list_files()
            file_info = next((f for f in files if f['id'] == file_id), None)
            
            if file_info is None:
                return None, "Archivo no encontrado"
                
            with open(file_info['ruta'], 'rb') as f:
                file_data = base64.b64encode(f.read()).decode('utf-8')
                
            return {
                'nombre': file_info['nombre'],
                'tipo': file_info['tipo'],
                'datos': file_data
            }, "Archivo encontrado"
        except Exception as e:
            return None, f"Error al descargar archivo: {str(e)}"

def main():
    server = MultimediaServer()
    
    # Iniciar el servidor Pyro4
    daemon = Pyro4.Daemon()
    ns = Pyro4.locateNS()
    uri = daemon.register(server)
    ns.register("multimedia.server", uri)
    
    print("Servidor multimedia iniciado...")
    daemon.requestLoop()

if __name__ == "__main__":
    main()