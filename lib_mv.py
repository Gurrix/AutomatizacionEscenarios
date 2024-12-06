import logging
import subprocess
import os
from lxml import etree

log = logging.getLogger('auto_p2')

# Directorio temporal
directorio_temporal = "/mnt/tmp/creativa1_g35"
  
class MV:
  def __init__(self, nombre):
    self.nombre = nombre
    log.debug('init MV ' + self.nombre)
 
  def crear_mv (self, imagen, interfaces_red, router):
    log.debug("crear_mv " + self.nombre)
  
    # Cargamos el fichero xml
    tree = etree.parse(f'{self.nombre}.xml')
    # Obtenemos el nodo raiz
    root = tree.getroot()
    # Verifica si la máquina es el balanceador (lb)
    if router:
      # Encuentra la sección de devices
      devices = root.find("./devices")
      # Encuentra la sección de interfaz
      interface = devices.find("./interface")
      # Duplica la interfaz
      new_interface = etree.SubElement(devices, "interface", type="bridge")
      new_source = etree.SubElement(new_interface, "source", bridge="LAN2")
      new_model = etree.SubElement(new_interface, "model", type="virtio")
      # Añade la interfaz duplicada al árbol
      devices.append(new_interface)
      # Guarda el árbol modificado en el nuevo archivo XML
      tree.write(f'{self.nombre}.xml', pretty_print=True)
    # Buscamos la etiqueta 'name' imprimimos su valor y luego lo cambiamos
    name = root.find("name")
    name.text = self.nombre        
    # Buscamos el nodo 'disk' bajo 'devices', imprimimos su valor y lo cambiamos
    disk = root.find("./devices/disk/source")
    ruta_completa = os.path.join(directorio_temporal, imagen)
    disk.set("file", ruta_completa)
    # Buscamos el nodo 'interface' bajo 'devices', imprimimos su valor y lo cambiamos
    interface = root.find("./devices/interface/source")
    interface.set("bridge", interfaces_red)
    # Guarda el árbol modificado en el nuevo archivo XML
    tree.write(f'{self.nombre}.xml', pretty_print=True)

    # Define la máquina virtual
    subprocess.call(['sudo', 'virsh', 'define', f'{self.nombre}.xml'])

    # Crear el contenido del archivo /etc/hostname
    with open(os.path.join(directorio_temporal, "hostname"), 'w') as hostname_file:
      hostname_file.write(f"{self.nombre}\n")

    # Crear el contenido del archivo /etc/network/interfaces
    if self.nombre == "s1":
       interfaces_content = "auto lo\niface lo inet loopback\nauto eth0\niface eth0 inet static\naddress 10.11.2.31\nnetmask 255.255.255.0\ngateway 10.11.2.1\n"
       with open(os.path.join(directorio_temporal, "interfaces"), 'w') as interfaces_file:
        interfaces_file.write(interfaces_content)
    elif self.nombre == "s2":
        interfaces_content = "auto lo\niface lo inet loopback\nauto eth0\niface eth0 inet static\naddress 10.11.2.32\nnetmask 255.255.255.0\ngateway 10.11.2.1\n"
        with open(os.path.join(directorio_temporal, "interfaces"), 'w') as interfaces_file:
          interfaces_file.write(interfaces_content)
    elif self.nombre == "s3":
        interfaces_content = "auto lo\niface lo inet loopback\nauto eth0\niface eth0 inet static\naddress 10.11.2.33\nnetmask 255.255.255.0\ngateway 10.11.2.1\n"
        with open(os.path.join(directorio_temporal, "interfaces"), 'w') as interfaces_file:
          interfaces_file.write(interfaces_content)
    elif self.nombre == "s4":
        interfaces_content = "auto lo\niface lo inet loopback\nauto eth0\niface eth0 inet static\naddress 10.11.2.34\nnetmask 255.255.255.0\ngateway 10.11.2.1\n"
        with open(os.path.join(directorio_temporal, "interfaces"), 'w') as interfaces_file:
          interfaces_file.write(interfaces_content)
    elif self.nombre == "s5":
        interfaces_content = "auto lo\niface lo inet loopback\nauto eth0\niface eth0 inet static\naddress 10.11.2.35\nnetmask 255.255.255.0\ngateway 10.11.2.1\n"
        with open(os.path.join(directorio_temporal, "interfaces"), 'w') as interfaces_file:
          interfaces_file.write(interfaces_content)
    elif self.nombre == "lb":
        interfaces_content = "auto lo\niface lo inet loopback\nauto eth0\niface eth0 inet static\naddress 10.11.1.1\nnetmask 255.255.255.0\ngateway 10.11.2.1\nauto eth1\niface eth1 inet static\naddress 10.11.2.1\nnetmask 255.255.255.0\ngateway 10.11.1.1\n"
        with open(os.path.join(directorio_temporal, "interfaces"), 'w') as interfaces_file:
          interfaces_file.write(interfaces_content)
    elif self.nombre == "c1":
        interfaces_content = "auto lo\niface lo inet loopback\nauto eth0\niface eth0 inet static\naddress 10.11.1.2\nnetmask 255.255.255.0\ngateway 10.11.1.1\n"
        with open(os.path.join(directorio_temporal, "interfaces"), 'w') as interfaces_file:
          interfaces_file.write(interfaces_content)

    # Copiar archivos al interior de la máquina virtual
    subprocess.call([f"sudo virt-copy-in -a {self.nombre}.qcow2 hostname /etc"], shell=True)
    subprocess.call([f"sudo virt-copy-in -a {self.nombre}.qcow2 interfaces /etc/network"], shell=True)
    
    # Configurar el balanceador de tráfico para que funcione como router al arrancar
    subprocess.call(["sudo virt-edit -a lb.qcow2 /etc/sysctl.conf -e 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/'"], shell=True)

    # Modificar el fichero /etc/hosts de las máquinas virtuales
    subprocess.call([f"sudo virt-edit -a {self.nombre}.qcow2 /etc/hosts -e 's/127.0.1.1.*/127.0.1.1 {self.nombre}/'"], shell=True)

  def arrancar_mv (self):
    log.debug("arrancar_mv " + self.nombre)
    # Arranca la máquina virtual
    subprocess.call(['sudo', 'virsh', 'start', self.nombre])

  def mostrar_consola_mv (self):
    log.debug("mostrar_mv " + self.nombre)
    # Abre un nuevo terminal para la MV
    subprocess.call(f"xterm -rv -sb -rightbar -fa monospace -fs 10 -title '{self.nombre}' -e 'sudo virsh console {self.nombre}' &", shell=True) 
    
  def parar_mv (self):
    log.debug("parar_mv " + self.nombre)
    # Para la máquina virtual
    subprocess.call(['sudo', 'virsh', 'shutdown', self.nombre])
    
  def liberar_mv (self):
    log.debug("liberar_mv " + self.nombre)
    # Detiene la máquina virtual
    subprocess.call(['sudo', 'virsh', 'destroy', self.nombre])
    # Elimina la definición de la máquina virtual
    subprocess.call(['sudo', 'virsh', 'undefine', self.nombre])
    # Elimina el archivo XML de la máquina virtual
    subprocess.call(["rm", f'{self.nombre}.xml', "-f"])
    # Eliminar el archivo de imagen de la máquina virtual (qcow2)
    subprocess.call(["rm", f'{self.nombre}.qcow2', "-f"])

    # Destrucción de los bridges correspondientes a las dos redes virtuales
    subprocess.call(["sudo ifconfig LAN1 down"], shell=True)
    subprocess.call(["sudo brctl delbr LAN1"], shell=True)
    subprocess.call(["sudo ifconfig LAN2 down"], shell=True)
    subprocess.call(["sudo brctl delbr LAN2"], shell=True)

  def mostrar_estado_mv(self):
    subprocess.call(['sudo', 'virsh', 'dominfo', self.nombre])
    # Utiliza el comando ping para verificar la conectividad con la MV
    if self.nombre == "s1":
      resultado_ping = subprocess.call(['ping', '-c', '1', '10.11.2.31'])
      if resultado_ping == 0:
        print(f"Conectividad con {self.nombre}: Exitosa")
      else:
        print(f"Conectividad con {self.nombre}: Fallida")
    elif self.nombre == "s2":
      resultado_ping = subprocess.call(['ping', '-c', '1', '10.11.2.32'])
      if resultado_ping == 0:
        print(f"Conectividad con {self.nombre}: Exitosa")
      else:
        print(f"Conectividad con {self.nombre}: Fallida")
    elif self.nombre == "s3":
      resultado_ping = subprocess.call(['ping', '-c', '1', '10.11.2.33'])
      if resultado_ping == 0:
        print(f"Conectividad con {self.nombre}: Exitosa")
      else:
        print(f"Conectividad con {self.nombre}: Fallida")
    elif self.nombre == "s4":
      resultado_ping = subprocess.call(['ping', '-c', '1', '10.11.2.34'])
      if resultado_ping == 0:
        print(f"Conectividad con {self.nombre}: Exitosa")
      else:
        print(f"Conectividad con {self.nombre}: Fallida")
    elif self.nombre == "s5":
      resultado_ping = subprocess.call(['ping', '-c', '1', '10.11.2.35'])
      if resultado_ping == 0:
        print(f"Conectividad con {self.nombre}: Exitosa")
      else:
        print(f"Conectividad con {self.nombre}: Fallida")
    elif self.nombre == "lb":
      resultado_ping = subprocess.call(['ping', '-c', '1', '10.11.1.1'])
      if resultado_ping == 0:
        print(f"Conectividad con {self.nombre}: Exitosa")
      else:
        print(f"Conectividad con {self.nombre}: Fallida")
    elif self.nombre == "c1":
      resultado_ping = subprocess.call(['ping', '-c', '1', '10.11.1.2'])
      if resultado_ping == 0:
        print(f"Conectividad con {self.nombre}: Exitosa")
      else:
        print(f"Conectividad con {self.nombre}: Fallida")    

class Red:
  def __init__(self, nombre):
    self.nombre = nombre
    log.debug('init Red ' + self.nombre)
    
  def crear_red(self):
      log.debug('crear_red ' + self.nombre)

  def liberar_red(self):
      log.debug('liberar_red ' + self.nombre)
