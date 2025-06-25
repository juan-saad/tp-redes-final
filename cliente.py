import requests
from requests.auth import HTTPBasicAuth

# URL base del servidor
BASE_URL = "http://192.168.1.4:8000"

# Credenciales para autenticación básica
AUTH = HTTPBasicAuth("admin", "admin123")


# Función para mostrar todos los premios
def get_mostrar_todos():
    r = requests.get(f"{BASE_URL}/")  # Endpoint raíz
    if r.ok:
        for p in r.json()['prizes']:
            print(f"{p['year']} - {p['category']}")  # Muestra año y categoría
    else:
        print("Error:", r.status_code, r.text)


# Función para buscar premios por año
def get_buscar_por_anio():
    year = input("Año: ")
    r = requests.get(f"{BASE_URL}/prizes/{year}", auth=AUTH)
    if r.ok:
        for p in r.json():
            print(f"{p['year']} - {p['category']}")
    else:
        print("Error:", r.status_code, r.text)

# Función para buscar premios por año y categoría
def get_buscar_por_anio_y_cat():
    year = input("Año: ")
    cat = input("Categoría: ")
    r = requests.get(f"{BASE_URL}/prizes/{year}/{cat}", auth=AUTH)
    if r.ok:
        premios = r.json()
        for p in premios:
            print(f"\n🎓 {p['year']} - {p['category']}")
            if 'laureates' in p:
                for l in p['laureates']:
                    print(f"  🧑 {l.get('firstname', '')} {l.get('surname', '')}")
                    print(f"     ➤ Motivación: {l.get('motivation', '')}")
                    print(f"     ➤ Share: {l.get('share', '')}")
            else:
                print("No hay laureados registrados.")
    else:
        print("Error:", r.status_code, r.text)

# Función para agregar un nuevo premio (puede incluir varios laureados)
def post_agregar_premio():
    year = int(input("Año: "))
    cat = input("Categoría: ")
    overallmotivation = input("Motivación general (opcional, enter para omitir): ").strip()

    laureates = []

    while True:
        print("\n-- Ingresando un laureado --")
        try:
            fname = input("Nombre: ")
            lname = input("Apellido: ")
            motivation = input("Motivación específica: ")
            share = input("Share: ")

            laureates.append({
                "firstname": fname,
                "surname": lname,
                "motivation": motivation,
                "share": share
            })

            continuar = input("¿Agregar otro laureado? (s/n): ").strip().lower()
            if continuar != "s":
                break
        except ValueError:
            print("Error: ID y Share deben ser números enteros.")

    data = {
        "year": year,
        "category": cat,
        "laureates": laureates
    }
   
    # Solo agregamos overallMotivation si fue ingresado
    if overallmotivation:
        data["overallMotivation"] = overallmotivation

    r = requests.post(f"{BASE_URL}/prize", json=data, auth=AUTH)
    if r.ok:
        print("Premio agregado correctamente.")
    else:
        print("Error:", r.status_code, r.text)



# Función para modificar un laureado dentro de un premio
def put_modificar_laureado():
    year = input("Año del premio: ")
    category = input("Categoría del premio: ")
    overall = input("Motivación general:")
    lid = input("ID del laureado a modificar: ")
    fname = input("Nuevo nombre: ")
    lname = input("Nuevo apellido: ")
    motivation = input("Nueva motivación: ")
    share = input("Nuevo share: ")

    # Datos nuevos del laureado
    data = {
        "laureates": [
            {
                "id": lid,
                "firstname": fname,
                "surname": lname,
                "motivation": motivation,
                "share": share
            }
        ],
        "overallMotivation": overall

    }

    # Se hace el PUT al endpoint con año y categoría 
    url = f"{BASE_URL}/prizes/{year}/{category}"
    r = requests.put(url, json=data, auth=AUTH)
    if r.ok:
        print("Laureado modificado.")
    else:
        print("Error:", r.status_code, r.text)


# Función para eliminar un premio completo (por año y categoría)
def delete_eliminar_premio():
    year = input("Año del premio a eliminar: ")
    category = input("Categoría del premio a eliminar: ")
    r = requests.delete(f"{BASE_URL}/prizes/{year}/{category}", auth=AUTH)
    if r.ok:
        print("Premio eliminado.")
    else:
        print("Error:", r.status_code, r.text)


# Menú interactivo principal
def menu():
    while True:
        print("\n--- MENÚ API PREMIOS ---")
        print("1. Ver todos los premios")
        print("2. Buscar por año")
        print("3. Buscar por año y categoría")
        print("4. Agregar nuevo premio")
        print("5. Modificar laureado")
        print("6. Eliminar premio")  
        print("0. Salir")

        opcion = input("Elegí una opción: ")

        if opcion == "1":
            get_mostrar_todos()
        elif opcion == "2":
            get_buscar_por_anio()
        elif opcion == "3":
            get_buscar_por_anio_y_cat()
        elif opcion == "4":
            post_agregar_premio()
        elif opcion == "5":
            put_modificar_laureado()
        elif opcion == "6":
            delete_eliminar_premio() 
        elif opcion == "0":
            print("¡Chau!")
            break
        else:
            print("Opción inválida. Probá de nuevo.")


# Punto de entrada del script
if __name__ == "__main__":
    menu()



# Punto de entrada del script
if __name__ == "__main__":
    menu()
