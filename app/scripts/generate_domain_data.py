# app/scripts/generate_domain_data.py
import asyncio
import random
from collections import defaultdict
from datetime import timedelta
from itertools import cycle

from bson import ObjectId

from app.config.database import mongo
from app.utils.helpers import utc_now

TARGET_COLLECTIONS = (
    "alojamiento",
    "guiaTuristico",
    "transporte",
    "proveedor",
    "seguroViaje",
    "viajeProgramado",
    "participante",
    "pago",
    "evaluaciones",
)

FIRST_NAMES = [
    "Sofia",
    "Mateo",
    "Valentina",
    "Santiago",
    "Camila",
    "Nicolas",
    "Isabella",
    "Juan Pablo",
    "Mariana",
    "Daniel",
    "Luciana",
    "Andres",
    "Catalina",
    "Sebastian",
    "Gabriela",
    "Tomas",
    "Laura",
    "Miguel",
    "Paula",
    "Alejandro",
]

LAST_NAMES = [
    "Gomez",
    "Rodriguez",
    "Martinez",
    "Garcia",
    "Lopez",
    "Hernandez",
    "Perez",
    "Sanchez",
    "Ramirez",
    "Torres",
    "Diaz",
    "Moreno",
    "Vargas",
    "Castro",
    "Rojas",
    "Mendoza",
]

SERVICE_TYPES = ["Hospedaje", "Transporte", "Alimentacion", "Actividades", "Seguros"]
LODGING_TYPES = ["Hotel", "Hostal", "Ecohotel", "Glamping", "Resort"]
TRANSPORT_TYPES = ["Bus", "Van", "Lancha", "Avion Regional", "Jeep 4x4"]
GUIDE_SPECIALTIES = [
    "historia colonial",
    "senderismo interpretativo",
    "fotografia de naturaleza",
    "gastronomia local",
    "turismo comunitario",
    "aventura y seguridad",
    "patrimonio cultural",
]
LANGUAGE_POOL = [
    ["Espanol"],
    ["Espanol", "Ingles"],
    ["Espanol", "Frances"],
    ["Espanol", "Ingles", "Portugues"],
]
PAYMENT_METHODS = ["Tarjeta", "PSE", "Transferencia", "Efectivo"]
PARTICIPANT_STATES = ["Confirmado", "Pendiente", "Cancelado"]
TRIP_STATES = ["Programado", "Confirmado", "Finalizado"]

EVALUATION_COMMENTS = [
    (
        "La experiencia estuvo muy bien coordinada desde el registro hasta el cierre del viaje. "
        "Los horarios se cumplieron, el guia conocia el destino con detalle y las actividades "
        "tuvieron un buen equilibrio entre descanso, cultura local y recorridos memorables."
    ),
    (
        "El paquete supero mis expectativas porque conecto lugares conocidos con experiencias "
        "pequenas y autenticas. La logistica de transporte fue clara, el alojamiento quedo cerca "
        "de los puntos principales y el grupo se sintio acompanado durante todo el itinerario."
    ),
    (
        "Fue un viaje muy completo para conocer el destino sin preocuparse por reservas o traslados. "
        "Me gusto especialmente la calidad humana del equipo local y la forma en que explicaron "
        "el contexto cultural antes de cada actividad."
    ),
    (
        "La relacion entre precio, servicios incluidos y acompanamiento fue adecuada. Hubo pequenos "
        "tiempos de espera en una actividad, pero el coordinador informo a tiempo y ofrecio una "
        "alternativa agradable mientras el grupo retomaba la ruta."
    ),
    (
        "Recomendaria el viaje a personas que quieran una experiencia organizada, con espacios para "
        "explorar por cuenta propia y momentos guiados de muy buena calidad. El destino quedo mejor "
        "explicado gracias a las historias y recomendaciones del guia."
    ),
]


def phone(prefix: str = "300") -> str:
    return f"+57 {prefix} {random.randint(1000000, 9999999)}"


def slugify(value: str) -> str:
    normalized = value.lower().replace(" ", ".").replace("/", ".")
    return "".join(char for char in normalized if char.isalnum() or char == ".")


def money(min_value: int, max_value: int, step: int = 10000) -> int:
    return random.randrange(min_value, max_value + step, step)


def package_price(paquete: dict) -> float:
    return float(paquete.get("precio") or paquete.get("precio_base") or 900000)


def package_name(paquete: dict) -> str:
    return paquete.get("titulo") or paquete.get("nombre") or "Paquete turistico"


def package_duration(paquete: dict) -> int:
    return int(paquete.get("duracion_dias") or 4)


def random_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


async def insert_many_if_any(collection, documents: list[dict]) -> int:
    if not documents:
        return 0
    result = await collection.insert_many(documents)
    return len(result.inserted_ids)


async def load_base_data(db) -> tuple[list[dict], list[dict]]:
    destinos = await db.destino.find({}).to_list(None)
    paquetes = await db.paqueteTuristico.find({}).to_list(None)

    if not destinos:
        raise RuntimeError("No hay destinos. Ejecuta primero app.scripts.generate_dataset.")
    if not paquetes:
        raise RuntimeError("No hay paquetes turisticos. Ejecuta primero app.scripts.generate_dataset.")

    return destinos, paquetes


def build_providers() -> list[dict]:
    providers = []
    service_cycle = cycle(SERVICE_TYPES)
    city_pool = [
        "Bogota",
        "Medellin",
        "Cartagena",
        "Santa Marta",
        "Pereira",
        "Cali",
        "Leticia",
        "Riohacha",
        "San Andres",
        "Bucaramanga",
    ]

    for index in range(65):
        service = next(service_cycle)
        city = random.choice(city_pool)
        name = f"{service} {random.choice(['Andes', 'Caribe', 'Origen', 'Nativa', 'Colombia', 'Ruta Viva'])} {index + 1:02d}"
        providers.append(
            {
                "_id": ObjectId(),
                "nombre": name,
                "tipo_servicio": service,
                "telefono": phone(random.choice(["300", "310", "315", "320"])),
                "email": f"contacto.{index + 1:02d}@{slugify(name)}.co",
                "ciudad": city,
                "calificacion": round(random.uniform(4.1, 4.9), 1),
                "contacto": {
                    "telefono": phone(random.choice(["300", "310", "315", "320"])),
                    "email": f"reservas.{index + 1:02d}@{slugify(name)}.co",
                    "ciudad": city,
                },
                "creado_en": utc_now(),
            }
        )
    return providers


def build_lodgings(destinos: list[dict], providers_by_service: dict[str, list[dict]]) -> list[dict]:
    lodgings = []
    lodging_providers = cycle(providers_by_service["Hospedaje"])

    for destino in destinos:
        for index in range(4):
            lodging_type = LODGING_TYPES[index % len(LODGING_TYPES)]
            provider = next(lodging_providers)
            stars = 2 if lodging_type == "Hostal" else random.randint(3, 5)
            price = money(90000, 780000)
            name = f"{lodging_type} {random.choice(['Mirador', 'Senderos', 'Boreal', 'Casa Real', 'Bahia', 'Reserva'])} {destino['nombre']}"
            lodgings.append(
                {
                    "nombre": name,
                    "destino_id": destino["_id"],
                    "proveedor_id": provider["_id"],
                    "tipo": lodging_type,
                    "categoria": f"{stars} estrellas",
                    "categoria_estrellas": stars,
                    "direccion": f"Cra. {random.randint(1, 80)} # {random.randint(1, 120)}-{random.randint(1, 99)}, sector turistico",
                    "telefono": phone(random.choice(["300", "311", "316"])),
                    "precio_noche": float(price),
                    "descripcion": (
                        f"{name} ofrece alojamiento comodo en {destino['nombre']}, con acceso practico "
                        "a rutas locales, desayuno regional y personal entrenado para viajeros nacionales "
                        "e internacionales."
                    ),
                    "creado_en": utc_now(),
                }
            )
    return lodgings


def build_guides(destinos: list[dict]) -> list[dict]:
    guides = []
    for destino in destinos:
        for index in range(3):
            name = random_name()
            guides.append(
                {
                    "nombre": name,
                    "especialidad": random.choice(GUIDE_SPECIALTIES),
                    "idiomas": random.choice(LANGUAGE_POOL),
                    "experiencia_anios": random.randint(3, 18),
                    "telefono": phone(random.choice(["301", "312", "317"])),
                    "email": f"{slugify(name)}.{slugify(destino['nombre'])}@guias.co",
                    "destino_id": destino["_id"],
                    "destinos": [destino["_id"]],
                    "calificacion": round(random.uniform(4.2, 5.0), 1),
                    "creado_en": utc_now(),
                }
            )
    return guides


def build_transport(destinos: list[dict], providers_by_service: dict[str, list[dict]]) -> list[dict]:
    transports = []
    transport_providers = cycle(providers_by_service["Transporte"])
    capacities = {"Bus": 38, "Van": 12, "Lancha": 18, "Avion Regional": 48, "Jeep 4x4": 6}

    for destino in destinos:
        for transport_type in random.sample(TRANSPORT_TYPES, 4):
            provider = next(transport_providers)
            transports.append(
                {
                    "tipo": transport_type,
                    "capacidad": capacities[transport_type] + random.randint(-2, 4),
                    "proveedor": provider["nombre"],
                    "proveedor_id": provider["_id"],
                    "destino_id": destino["_id"],
                    "precio_base": float(money(60000, 680000)),
                    "descripcion": (
                        f"Servicio de {transport_type.lower()} para traslados turisticos en {destino['nombre']}, "
                        "con conductores locales, soporte de equipaje y rutas coordinadas con los paquetes."
                    ),
                    "creado_en": utc_now(),
                }
            )
    return transports


def build_insurance(providers_by_service: dict[str, list[dict]]) -> list[dict]:
    insurance_docs = []
    insurance_providers = cycle(providers_by_service["Seguros"])
    coverage_options = [
        ["Asistencia medica", "Cancelacion de viaje", "Equipaje"],
        ["Emergencias", "Traslado hospitalario", "Deportes recreativos"],
        ["Asistencia 24/7", "Medicamentos", "Perdida de documentos"],
        ["Accidentes", "Responsabilidad civil", "Interrupcion de viaje"],
    ]

    for index in range(30):
        provider = next(insurance_providers)
        coverage = random.choice(coverage_options)
        insurance_docs.append(
            {
                "nombre": f"Seguro Viajero {random.choice(['Esencial', 'Plus', 'Total', 'Aventura'])} {index + 1:02d}",
                "cobertura": coverage,
                "precio": float(money(45000, 260000, 5000)),
                "proveedor_id": provider["_id"],
                "vigencia_dias": random.choice([4, 5, 7, 10, 15]),
                "creado_en": utc_now(),
            }
        )
    return insurance_docs


def build_trips(paquetes: list[dict]) -> list[dict]:
    trips = []
    start_anchor = utc_now().date() - timedelta(days=150)
    selected_packages = [paquetes[index % len(paquetes)] for index in range(200)]

    for index, paquete in enumerate(selected_packages):
        trip_start = start_anchor + timedelta(days=index * 3 + random.randint(0, 2))
        duration = package_duration(paquete)
        trip_end = trip_start + timedelta(days=duration - 1)
        state = "Finalizado" if trip_end < utc_now().date() else random.choice(TRIP_STATES[:2])
        total_slots = random.randint(14, 36)
        trips.append(
            {
                "_id": ObjectId(),
                "paquete_id": paquete["_id"],
                "paquete_nombre": package_name(paquete),
                "fecha_inicio": trip_start,
                "fecha_fin": trip_end,
                "cupos_totales": total_slots,
                "cupos_disponibles": total_slots,
                "estado": state,
                "creado_en": utc_now(),
            }
        )
    return trips


def build_participants_and_payments(trips: list[dict], packages_by_id: dict[ObjectId, dict]) -> tuple[list[dict], list[dict]]:
    participants = []
    payments = []

    for trip in trips:
        target_count = random.randint(3, 7)
        if random.random() < 0.35:
            target_count += random.randint(1, 4)

        occupied_slots = 0
        for _ in range(min(target_count, trip["cupos_totales"])):
            participant_id = ObjectId()
            name = random_name()
            state = random.choices(PARTICIPANT_STATES, weights=[0.74, 0.18, 0.08], k=1)[0]
            if state != "Cancelado":
                occupied_slots += 1

            participant = {
                "_id": participant_id,
                "nombre": name,
                "correo": f"{slugify(name)}.{str(participant_id)[-6:]}@correo.com",
                "telefono": phone(random.choice(["300", "313", "318", "321"])),
                "viaje_programado_id": trip["_id"],
                "viaje_id": trip["_id"],
                "fecha_registro": utc_now() - timedelta(days=random.randint(2, 120)),
                "estado": state,
                "contacto": {
                    "email": f"{slugify(name)}.{str(participant_id)[-6:]}@correo.com",
                    "telefono": phone(random.choice(["300", "313", "318", "321"])),
                },
                "preferencias": random.sample(
                    ["naturaleza", "gastronomia", "historia", "fotografia", "descanso", "aventura"],
                    k=random.randint(1, 3),
                ),
                "creado_en": utc_now(),
            }
            participants.append(participant)

            package = packages_by_id[trip["paquete_id"]]
            base_value = package_price(package)
            multiplier = 0.35 if state == "Pendiente" else 1.0
            if state == "Cancelado":
                payment_state = random.choice(["Reembolsado", "Pendiente"])
                multiplier = 0.2 if payment_state == "Reembolsado" else 0.0
            else:
                payment_state = "Pagado" if state == "Confirmado" else "Pendiente"

            amount = round(base_value * multiplier, 2)
            payments.append(
                {
                    "participante_id": participant_id,
                    "viaje_id": trip["_id"],
                    "valor": amount,
                    "monto": amount,
                    "moneda": "COP",
                    "metodo_pago": random.choice(PAYMENT_METHODS),
                    "estado": payment_state,
                    "fecha_pago": utc_now() - timedelta(days=random.randint(0, 90)),
                    "creado_en": utc_now(),
                }
            )

        trip["cupos_disponibles"] = max(trip["cupos_totales"] - occupied_slots, 0)

    return participants, payments


def build_evaluations(participants: list[dict], trips_by_id: dict[ObjectId, dict]) -> list[dict]:
    eligible = [
        participant
        for participant in participants
        if participant["estado"] == "Confirmado"
        and trips_by_id[participant["viaje_programado_id"]]["estado"] in {"Confirmado", "Finalizado"}
    ]
    random.shuffle(eligible)
    selected = eligible[: min(700, len(eligible))]
    evaluations = []

    for participant in selected:
        trip = trips_by_id[participant["viaje_programado_id"]]
        score = random.choices([3, 4, 5, 2, 1], weights=[0.14, 0.38, 0.43, 0.04, 0.01], k=1)[0]
        evaluation_date = utc_now() - timedelta(days=random.randint(0, 60))
        evaluations.append(
            {
                "consulta_id": f"viaje:{trip['_id']}:participante:{participant['_id']}",
                "participante_id": participant["_id"],
                "viaje_programado_id": trip["_id"],
                "viaje_id": trip["_id"],
                "puntuacion": score,
                "comentario": random.choice(EVALUATION_COMMENTS),
                "fecha": evaluation_date,
                "fecha_evaluacion": evaluation_date,
            }
        )
    return evaluations


async def main() -> None:
    random.seed(20260612)

    print("Iniciando conexion a MongoDB...")
    await mongo.connect()
    db = mongo.database

    destinos, paquetes = await load_base_data(db)
    packages_by_id = {paquete["_id"]: paquete for paquete in paquetes}

    print("Limpiando colecciones de dominio generadas previamente...")
    for collection_name in TARGET_COLLECTIONS:
        await db[collection_name].delete_many({})

    providers = build_providers()
    providers_by_service = defaultdict(list)
    for provider in providers:
        providers_by_service[provider["tipo_servicio"]].append(provider)

    lodgings = build_lodgings(destinos, providers_by_service)
    guides = build_guides(destinos)
    transports = build_transport(destinos, providers_by_service)
    insurance_docs = build_insurance(providers_by_service)
    trips = build_trips(paquetes)
    participants, payments = build_participants_and_payments(trips, packages_by_id)
    trips_by_id = {trip["_id"]: trip for trip in trips}
    evaluations = build_evaluations(participants, trips_by_id)

    print("Insertando documentos por lotes...")
    stats = {
        "proveedor": await insert_many_if_any(db.proveedor, providers),
        "alojamiento": await insert_many_if_any(db.alojamiento, lodgings),
        "guiaTuristico": await insert_many_if_any(db.guiaTuristico, guides),
        "transporte": await insert_many_if_any(db.transporte, transports),
        "seguroViaje": await insert_many_if_any(db.seguroViaje, insurance_docs),
        "viajeProgramado": await insert_many_if_any(db.viajeProgramado, trips),
        "participante": await insert_many_if_any(db.participante, participants),
        "pago": await insert_many_if_any(db.pago, payments),
        "evaluaciones": await insert_many_if_any(db.evaluaciones, evaluations),
    }

    print("\n--- ESTADISTICAS FINALES ---")
    for collection_name in TARGET_COLLECTIONS:
        total = await db[collection_name].count_documents({})
        inserted = stats.get(collection_name, 0)
        print(f"{collection_name}: {total} documentos ({inserted} insertados)")

    print("\n--- POBLACION DE DOMINIO TURISTICO COMPLETADA ---")
    await mongo.close()


if __name__ == "__main__":
    asyncio.run(main())
