#!/usr/bin/env python

from lib_mv import MV
from lib_mv import Red
import logging
import sys
import subprocess
import os
import json

def init_log():
    # Creacion y configuracion del logger
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger('auto_p2')
    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
    ch.setFormatter(formatter)
    log.addHandler(ch)
    log.propagate = False

def pause():
    p = input("Press <ENTER> key to continue...")

# Main
init_log()
print('CDPS - mensaje info1')

# Directorio actual
directorio_actual = os.getcwd()

# Volver al directorio raíz del sistema de archivos
os.chdir("/")

# Cambiar al directorio /mnt/tmp
os.chdir("/mnt/tmp")

# Crear el directorio del usuario en /mnt/tmp (si no está ya creado)
if not os.path.exists("creativa1_g35"):
    os.makedirs("creativa1_g35")

# Cambiar al directorio del usuario
os.chdir("creativa1_g35")
directorio_temporal = os.getcwd()

# Copiar la imagen base de la máquina virtual y descomprimirla
if not os.path.exists("cdps-vm-base-pc1.qcow2"):
    subprocess.call([f'cp /{directorio_actual}/cdps-vm-base-pc1.qcow2 .'], shell=True)

# Copiar la plantilla de definición de VMs
if not os.path.exists("plantilla-vm-pc1.xml"):
    subprocess.call([f'cp /{directorio_actual}/plantilla-vm-pc1.xml .'], shell=True)
    
# Parámetro obligatorio que definirá la operación a realizar
modo_ejecucion = sys.argv[1]

# Lee el archivo JSON
json_path = os.path.join(directorio_actual, 'auto-p2.json')
with open(json_path, 'r') as archivo_json:
    configuracion = json.load(archivo_json)

# Accede al valor del número de servidores
num_serv = configuracion.get('num_serv')

# Comprueba que el valor sea correcto
if num_serv is None or not isinstance(num_serv, int) or num_serv < 1 or num_serv > 5:
    print("Error: El valor del número de servidores en el archivo json de configuración es incorrecto.")
    sys.exit(1)  # Salir con código de error 1
else:
    print(f"**************************Número de servidores: {num_serv}***************************")

# Ahora, 'num_serv' contiene el valor del número de servidores que puedes usar en tu script.

lb = MV('lb')
c1 = MV('c1')
servidores = []
servidor_names = []

# Crear instancias de MV con nombres dinámicos
for i in range(1, num_serv+1):
    nombre_servidor = f's{i}' 
    servidores.append(MV(nombre_servidor))
    servidor_names.append(nombre_servidor)

# Ahora, la lista 'servidores' contiene las instancias de MV con nombres s1, s2, s3, ...

lan1 = Red('lan1')
lan2 = Red('lan2')

# Operación: crear
if modo_ejecucion == "crear":

    # Creación de los sistemas de ficheros COW que utilizará cada una de las MVs del escenario
    for name in servidor_names:
        subprocess.call([f'qemu-img create -f qcow2 -b cdps-vm-base-pc1.qcow2 {name}.qcow2'], shell=True)
    subprocess.call(["qemu-img create -f qcow2 -b cdps-vm-base-pc1.qcow2 lb.qcow2"], shell=True)
    subprocess.call(["qemu-img create -f qcow2 -b cdps-vm-base-pc1.qcow2 c1.qcow2"], shell=True)

    # Creación del fichero XML de especificación de cada MV partiendo de la plantilla
    for name in servidor_names:
        subprocess.call([f'cp plantilla-vm-pc1.xml {name}.xml'], shell=True)
    subprocess.call(["cp plantilla-vm-pc1.xml lb.xml"], shell=True)
    subprocess.call(["cp plantilla-vm-pc1.xml c1.xml"], shell=True)
    
    # Creación de los bridges correspondientes a las dos redes virtuales
    subprocess.call(["sudo brctl addbr LAN1"], shell=True)
    subprocess.call(["sudo ifconfig LAN1 up"], shell=True)
    subprocess.call(["sudo brctl addbr LAN2"], shell=True)
    subprocess.call(["sudo ifconfig LAN2 up"], shell=True)

    # Configuración de red de cada una de las máquinas virtuales **** Solo está configurado el Host 
    subprocess.call(["sudo ifconfig LAN1 10.11.1.3/24"], shell=True)
    subprocess.call(["sudo ip route add 10.11.0.0/16 via 10.11.1.1"], shell=True)
    
    # Arranque del gestor de máquinas virtuales
    subprocess.call(["HOME=/mnt/tmp sudo virt-manager"], shell=True)

    # Creación de las máquinas virtuales utilizando el comando virsh
    for servidor in servidores:
        servidor.crear_mv(f'{servidor.nombre}.qcow2', 'LAN2', False)
    lb.crear_mv('lb.qcow2', 'LAN1', True)
    c1.crear_mv('c1.qcow2', 'LAN1', False)

# Operación: arrancar
elif modo_ejecucion == "arrancar":
    
    if len(sys.argv) == 2:
        # Arranque de las máquinas virtuales utilizando el comando virsh
        for servidor in servidores:
            servidor.arrancar_mv()
        lb.arrancar_mv()
        c1.arrancar_mv()

        # Acceso a las MV a través de la consola textual
        for servidor in servidores:
            servidor.mostrar_consola_mv()
        lb.mostrar_consola_mv()
        c1.mostrar_consola_mv()
    
    elif len(sys.argv) == 3:
        mv_nombre = sys.argv[2]  # Obtiene el nombre de la MV desde el segundo parámetro

        # Busca la MV con el nombre proporcionado
        mv_a_arrancar = None
        for servidor in servidores + [lb, c1]:
            if servidor.nombre == mv_nombre:
                mv_a_arrancar = servidor
                break

        if mv_a_arrancar is None:
            print(f"Error: No se encontró ninguna MV con el nombre '{mv_nombre}'.")
            sys.exit(1)

        # Arranca la MV específica
        mv_a_arrancar.arrancar_mv()
        # Muestra la consola de la MV específica
        mv_a_arrancar.mostrar_consola_mv()
    
    else:
        print("Error: Número incorrecto de argumentos.")
        sys.exit(1)
    
# Operación: parar
elif modo_ejecucion == "parar":

    if len(sys.argv) == 2:
        # Pausa de las máquinas virtuales utilizando el comando virsh
        for servidor in servidores:
            servidor.parar_mv()
        lb.parar_mv()
        c1.parar_mv()

    elif len(sys.argv) == 3:
        mv_nombre = sys.argv[2]  # Obtiene el nombre de la MV desde el segundo parámetro

        # Busca la MV con el nombre proporcionado
        mv_a_parar = None
        for servidor in servidores + [lb, c1]:
            if servidor.nombre == mv_nombre:
                mv_a_parar = servidor
                break

        if mv_a_parar is None:
            print(f"Error: No se encontró ninguna MV con el nombre '{mv_nombre}'.")
            sys.exit(1)

        # Para la MV específica
        mv_a_parar.parar_mv()
    
    else:
        print("Error: Número incorrecto de argumentos.")
        sys.exit(1)
    
# Operación: liberar
elif modo_ejecucion == "liberar":

    # Liberación de las máquinas virtuales utilizando el comando virsh
    for servidor in servidores:
        servidor.liberar_mv()
    lb.liberar_mv()
    c1.liberar_mv()

# Operación: monitor
elif modo_ejecucion == "monitor":

    # Monitorización del escenario
    for servidor in servidores:
        servidor.mostrar_estado_mv()
    lb.mostrar_estado_mv()
    c1.mostrar_estado_mv()
