# app/scripts/generate_dataset.py
import asyncio
import random
from app.config.database import mongo
from app.utils.helpers import utc_now
from app.utils.multimedia_assets import build_multimedia_document, iter_destination_images

DESTINOS_DATA = [
    {
        "nombre": "Cartagena",
        "descripcion": "Ciudad colonial amurallada con playas caribeñas, historia viva de la época de la colonia y una vibrante gastronomía gourmet internacional. Ideal para explorar castillos, murallas antiguas, la arquitectura republicana y disfrutar de islas paradisíacas como las Islas del Rosario y Barú en un ambiente cálido y festivo durante todo el año.",
        "categoria": "playa",
        "tags": ["historia", "playa", "gastronomia", "romantico", "caribe", "arquitectura", "cultura", "patrimonio"]
    },
    {
        "nombre": "San Andrés",
        "descripcion": "Isla paradisíaca en el mar Caribe conocida por su mar de los siete colores que exhibe tonalidades turquesas y azules. Es el lugar perfecto para actividades acuáticas avanzadas como el buceo autónomo, snorkeling en barreras de coral intactas, deportes náuticos y un descanso absoluto bajo palmeras en playas de arena blanca y fina con influencia cultural raizal.",
        "categoria": "playa",
        "tags": ["playa", "buceo", "descanso", "mar", "acuatico", "snorkeling", "isla", "relax"]
    },
    {
        "nombre": "Santa Marta",
        "descripcion": "Un destino único en el mundo donde la imponente Sierra Nevada (la montaña costera más alta del mundo) se encuentra directamente con las aguas del mar Caribe. Ofrece una asombrosa biodiversidad, senderismo ecológico sagrado dentro del Parque Nacional Natural Tayrona, playas exóticas rodeadas de selva tropical, restos arqueológicos precolombinos e historia colonial.",
        "categoria": "playa",
        "tags": ["playa", "naturaleza", "senderismo", "cultura", "aventura", "ecotermal", "sierra", "trekking"]
    },
    {
        "nombre": "Bogotá",
        "descripcion": "Capital cosmopolita y vibrante de Colombia situada en los Andes orientales a 2600 metros sobre el nivel del mar. Posee una enorme y variada oferta cultural que incluye museos de clase mundial como el Museo del Oro y el Museo de Botero, un centro histórico colonial en La Candelaria, centros de negocios internacionales, vida nocturna de vanguardia y gastronomía de altura.",
        "categoria": "ciudad",
        "tags": ["cultura", "museos", "negocios", "gastronomia", "urbano", "historia", "capital", "entretenimiento"]
    },
    {
        "nombre": "Medellín",
        "descripcion": "Conocida globalmente como la ciudad de la eterna primavera debido a su clima templado sumamente agradable. Es famosa por sus procesos de innovación social, urbanismo integrado con sistemas como el Metrocable, una rica cultura paisa, festivales masivos como la Feria de las Flores, una activa vida nocturna en El Poblado y hermosos paisajes de montaña.",
        "categoria": "ciudad",
        "tags": ["innovacion", "clima", "rumba", "cultura", "urbano", "paisa", "transformacion", "parques"]
    },
    {
        "nombre": "Eje Cafetero",
        "descripcion": "Paisaje Cultural Cafetero declarado Patrimonio de la Humanidad. Caracterizado por sus colinas verdes tapizadas de cafetales, fincas tradicionales donde se aprende el proceso artesanal del café, la imponente naturaleza del Valle de Cocora con sus gigantescas palmas de cera, pueblos coloridos con arquitectura de colonización antioqueña y relajantes aguas termales naturales.",
        "categoria": "naturaleza",
        "tags": ["cafe", "naturaleza", "senderismo", "familia", "tradicion", "patrimonio", "termales", "pueblos"]
    },
    {
        "nombre": "Amazonas",
        "descripcion": "Una inmersión total en el pulmón del mundo partiendo desde Leticia. Ofrece el avistamiento místico de delfines rosados y grises en el río Amazonas, caminatas nocturnas para observar fauna exótica e insectos bioluminiscentes, convivencia con comunidades indígenas ancestrales (Tikuna y Yagua), lagos mágicos cubiertos de lotos gigantes y reservas ecológicas de selva profunda inundable.",
        "categoria": "naturaleza",
        "tags": ["selva", "biodiversidad", "ecoturismo", "indigenas", "aventura", "rio", "fauna", "exotico"]
    },
    {
        "nombre": "La Guajira",
        "descripcion": "Un territorio desértico imponente y místico en el extremo norte de Suramérica que se funde directamente con el oleaje del mar Caribe. Permite la inmersión cultural en las rancherías de la comunidad indígena Wayúu, la exploración de dunas de arena gigantescas que caen al mar en Taroa, avistamiento de flamencos rosados y los paisajes sagrados del Cabo de la Vela y Punta Gallinas.",
        "categoria": "aventura",
        "tags": ["desierto", "cultura", "playa", "viento", "exotico", "indigenas", "dunas", "paisaje"]
    },
    {
        "nombre": "Villa de Leyva",
        "descripcion": "Pueblo colonial perfectamente conservado y congelado en el tiempo. Cuenta con una de las plazas empedradas más grandes de toda América, rodeada de edificaciones de fachadas blancas y balcones de madera colonial. Ofrece un ambiente bohemio, romántico y tranquilo, zonas de yacimientos paleontológicos con fósiles de dinosaurios marinos y desiertos cercanos para la observación astronómica.",
        "categoria": "pueblo",
        "tags": ["historia", "arquitectura", "romantico", "tranquilidad", "fosiles", "colonial", "astronomiia", "pueblo"]
    },
    {
        "nombre": "Barichara",
        "descripcion": "Considerado unánimemente el pueblo más hermoso y estético de Colombia. Esculpido por completo en piedra amarilla por artesanos locales, ofrece un entorno idílico para el descanso absoluto, la fotografía arquitectónica y largas caminatas por senderos coloniales reales como el Camino Real hacia Guane. Su gastronomía exótica destaca por las hormigas culonas y platos tradicionales santandereanos.",
        "categoria": "pueblo",
        "tags": ["arquitectura", "tranquilidad", "artesanias", "historia", "romantico", "piedra", "senderos", "paz"]
    },
    {
        "nombre": "Cali",
        "descripcion": "La vibrante capital mundial de la salsa, una ciudad rebosante de ritmo, alegría y movimiento. Destaca por sus escuelas de baile galardonadas internacionalmente, espectáculos nocturnas electrizantes, una rica gastronomía influenciada por la cultura del Pacífico colombiano y un clima cálido suavizado en las tardes por la brisa fresca que desciende de los Farallones de Cali.",
        "categoria": "ciudad",
        "tags": ["salsa", "baile", "gastronomia", "calor", "cultura", "pacifico", "rumba", "alegria"]
    },
    {
        "nombre": "Popayán",
        "descripcion": "Conocida como la ciudad blanca debido al color uniforme de sus construcciones coloniales en el centro histórico. Es mundialmente famosa por sus solemnes y tradicionales procesiones de Semana Santa declaradas patrimonio inmaterial, y por ser la primera ciudad de la UNESCO en gastronomía gracias a sus deliciosas recetas tradicionales andinas y pipián.",
        "categoria": "pueblo",
        "tags": ["historia", "religion", "arquitectura", "gastronomia", "blanca", "patrimonio", "colonial", "tradicion"]
    },
    {
        "nombre": "Canyon del Chicamocha",
        "descripcion": "Un imponente y profundo accidente geográfico que ofrece uno de los paisajes secos más espectaculares de América Latina. Es el escenario ideal para la práctica de deportes extremos de aventura como el vuelo en parapente aprovechando las corrientes térmicas, el rafting en el río Chicamocha, el columpio extremo y el teleférico que cruza el cañón conectando con el parque Panachi.",
        "categoria": "aventura",
        "tags": ["aventura", "parapente", "naturaleza", "extremo", "vistas", "cañon", "rafting", "sanderismo"]
    },
    {
        "nombre": "Nuquí",
        "descripcion": "Un paraíso natural virgen e inexplorado localizado geográficamente entre la densa selva tropical del Chocó y las salvajes aguas del océano Pacífico. Es reconocido internacionalmente por ser la sala de maternidad de las majestuosas ballenas jorobadas entre julio y octubre. Cuenta con playas de arena negra, cascadas termales junto al mar, surf de clase mundial y ecoturismo de conservación.",
        "categoria": "naturaleza",
        "tags": ["ballenas", "pacifico", "selva", "virgen", "ecoturismo", "surf", "termales", "afrodescendientes"]
    },
    {
        "nombre": "Providencia",
        "descripcion": "Una joya caribeña de origen volcánico que se mantiene virgen, colorida y desconectada del turismo de masas. Posee el tercer arrecife de barrera coralina más largo del planeta Tierra, lo que garantiza condiciones de buceo inigualables. Su arquitectura típica isleña está construida en madera de vivos colores y su población conserva tradiciones anglo-caribeñas e idioma creole.",
        "categoria": "playa",
        "tags": ["tranquilidad", "buceo", "caribe", "isla", "exclusivo", "arrecife", "naturaleza", "aislado"]
    },
    {
        "nombre": "Guatapé",
        "descripcion": "Un pintoresco pueblo andino famoso por los zócalos de colores brillantes tallados en las bases de las fachadas de sus casas, los cuales narran historias locales. Se encuentra junto a un gigantesco embalse artificial de aguas verdosas donde se practican deportes náuticos. El atractivo principal es El Peñón de Guatapé, un monolito de piedra de 220 metros con más de 700 escalones.",
        "categoria": "pueblo",
        "tags": ["represa", "vistas", "colores", "familia", "fotografia", "monolito", "pueblo", "zocalos"]
    },
    {
        "nombre": "Desierto de la Tatacoa",
        "descripcion": "La segunda zona árida más extensa de Colombia, dividida en un laberinto de formaciones de tierra de color ocre (sector Cuzco) y gris (sector Los Hoyos). Al no tener contaminación lumínica ni auditiva, es considerado un observatorio astronómico natural excepcional para contemplar constelaciones, lluvias de estrellas y planetas. Cuenta con piscinas de agua mineral en medio del desierto.",
        "categoria": "aventura",
        "tags": ["astronomia", "desierto", "estrellas", "fotografia", "paisaje", "erosion", "paleontologia", "senderos"]
    },
    {
        "nombre": "Cabo de la Vela",
        "descripcion": "Lugar sagrado y mitológico para la etnia indígena Wayúu, donde según sus creencias descansan las almas de los difuntos. El paisaje es un contraste radical donde el desierto plano muere directamente en un mar turquesa y tranquilo. Es un destino mundial para los deportistas de kitesurf y windsurf debido a la velocidad constante y los vientos potentes alisios.",
        "categoria": "aventura",
        "tags": ["mar", "desierto", "kitesurf", "indigenas", "desconexion", "viento", "playa", "misticismo"]
    },
    {
        "nombre": "Pasto y Laguna de la Cocha",
        "descripcion": "Asentado en las faldas del imponente volcán Galeras, destaca por su rica herencia cultural andina, artesanías únicas en barniz de Pasto y el multitudinario Carnaval de Negros y Blancos. A pocos kilómetros se encuentra el humedal Ramsar de la Laguna de la Cocha, un cuerpo de agua místico de origen glacial que alberga la pequeña Isla de La Corota, rica en flora endémica.",
        "categoria": "naturaleza",
        "tags": ["cultura", "frio", "laguna", "carnaval", "paisaje", "andes", "artesanias", "volcan"]
    },
    {
        "nombre": "Caño Cristales",
        "descripcion": "Ampliamente catalogado por exploradores como el río más hermoso del mundo o el río de los siete colores que corre en la Serranía de la Macarena. Durante los meses de invierno y primavera, la planta acuática endémica Macarenia clavigera tiñe el fondo del cauce con intensos tonos rojos, rosados, verdes y amarillos, creando un espectáculo visual natural sin paralelo en el planeta.",
        "categoria": "naturaleza",
        "tags": ["rio", "colores", "exclusivo", "fotografia", "senderismo", "macarena", "conservacion", "endemico"]
    }
]

TIPOS_PAQUETE = ["Aventura", "Romántico", "Familiar", "Premium", "Económico"]

ITINERARIOS_POOL = {
    "Aventura": (
        "Día 1: Expedición Extrema y Supervivencia. Arribo directo al destino geográfico e instalación formal en nuestro campamento base especializado. "
        "Reunión técnica de seguridad de alta montaña con guías certificados y entrega formal de equipos técnicos. "
        "Por la tarde, realizaremos una fuerte caminata de aclimatación por senderos de pendiente pronunciada, evaluando la resistencia aeróbica del grupo. "
        "Aprenderemos nociones básicas de navegación terrestre y orientación estelar. Al caer la noche, disfrutaremos de una cena energética "
        "alrededor de una gran fogata comunitaria, compartiendo relatos técnicos de expediciones previas en entornos hostiles e inhóspitos.\n"
        "Día 2: Desafío de Altura y Descenso Vertical. Desayuno calórico balanceado antes del amanecer. Iniciamos la travesía de senderismo técnico "
        "de alto rendimiento, cruzando puentes colgantes sobre cañones profundos y abriéndonos paso por zonas de vegetación densa y húmeda. "
        "Al mediodía, haremos una parada estratégica para consumir un almuerzo energético de campaña de absorción rápida. En la tarde, iniciaremos "
        "la sesión de rappel técnico sobre paredes de roca caliza natural de más de 35 metros de altura, bajo supervisión milimétrica. "
        "Regreso guiado al campamento base para una sesión de recuperación y descanso en hamacas o tiendas de campaña de alta montaña.\n"
        "Día 3: Descenso Fluvial en Rápidos e Hidrografía. Jornada completa dedicada exclusivamente a la adrenalina y la exploración de corrientes de agua. "
        "Abordaremos las balsas de rafting profesional para iniciar un vertiginoso descenso por rápidos fluviales clasificados en niveles III y IV, "
        "lo que demandará concentración máxima y un sólido trabajo coordinado en equipo. Tras el almuerzo típico ribereño, cambiaremos al equipo "
        "de espeleología y nos adentraremos con linternas frontales y cascos en un intrincado sistema de cavernas y túneles subterráneos inundados, "
        "admirando formaciones geológicas de estalactitas formadas durante millones de años.\n"
        "Día 4: Reconocimiento Aéreo, Conclusiones y Retorno. Ascenso matutino al mirador geográfico más elevado de la zona para capturar fotografías "
        "panorámicas a la luz del amanecer. Realizaremos un taller práctico de supervivencia y armado de refugios naturales con elementos del entorno. "
        "Almuerzo típico de clausura con técnicas culinarias locales sobre fuegos abiertos. Evaluación final de la ruta con los guías, entrega de insignias "
        "simbólicas de expedición aprobada y traslado logístico coordinado hacia los aeropuertos o terminales para el viaje de regreso."
    ),
    "Romántico": (
        "Día 1: Bienvenida de Ensueño y Alta Cocina Privada. Llegada exclusiva al hotel boutique de diseño colonial seleccionado especialmente "
        "para parejas. Recibimiento personalizado con copas de champaña helada y frutas de la región. Registro de habitación prioritario con ingreso "
        "a una suite máster decorada minuciosamente con pétalos frescos de rosas, iluminación tenue de velas aromáticas y sábanas de hilo egipcio. "
        "Al anochecer, se servirá una cena gourmet romántica privada de cuatro tiempos elaborada por un chef exclusivo, dispuesta en una terraza privada "
        "con vistas panorámicas inigualables y música de cuerdas en vivo.\n"
        "Día 2: Picnic de Lujo e Inmersión en Paisajes Pintorescos. Desayuno continental gourmet servido de forma privada en la cama. A media mañana, "
        "un conductor privado los trasladará hacia un santuario natural aislado o un viñedo local. Allí disfrutarán de un picnic de alta gama configurado "
        "con una selección fina de quesos madurados, carnes frías artesanales, panadería francesa, frutas frescas de la estación y una botella de vino tinto "
        "reserva seleccionado. Tarde libre programada para caminar sin prisas por los rincones históricos más mágicos, coloniales y fotogénicos del destino.\n"
        "Día 3: Bienestar Absoluto en Pareja y Atardecer Místico. Mañana dedicada enteramente a la relajación y renovación energética en el spa premium "
        "del hotel. El circuito iniciará con hidroterapia en un jacuzzi privado enriquecido con sales minerales, seguido de un masaje terapéutico relajante "
        "corporal completo simultáneo en pareja utilizando aceites esenciales de aromaterapia de 90 minutos. Al finalizar la tarde, embarque en un velero "
        "o acceso a un mirador VIP reservado para presenciar la caída del sol mientras se realiza un brindis con vino espumoso y fresas con chocolate.\n"
        "Día 4: Amanecer Sereno, Despedida y Detalles Memorables. Sesión opcional de yoga o meditación guiada en pareja al aire libre para recibir "
        "las primeras luces del día en perfecta armonía. Desayuno buffet de gala en los jardines principales del hotel. Tiempo libre para disfrutar de "
        "las piscinas de borde infinito, tomar fotografías de pareja con vestuario tradicional o adquirir joyería artesanal local exclusiva de recuerdo. "
        "Proceso de salida tardía (late check-out) asistido por conserjería y traslado privado premium hacia su terminal de partida."
    ),
    "Familiar": (
        "Día 1: Integración Familiar y Confort desde el Arribo. Cálido recibimiento de todo el núcleo familiar por parte de nuestro coordinador "
        "y guía recreativo bilingüe en los puntos de llegada pactados. Traslado en una cómoda minivan ejecutiva privada totalmente equipada con aire "
        "acondicionado, pantallas de entretenimiento y sistemas de retención infantil para la seguridad de niños y comodidad de adultos mayores. "
        "Registro ágil en el resort familiar que cuenta con parques acuáticos internos y clubes infantiles. Cena buffet temática de bienvenida adaptada.\n"
        "Día 2: Aventura Didáctica, Parques y Naturaleza Viva. Desayuno buffet familiar completo y nutritivo. Salida grupal hacia el parque temático, "
        "parque de diversiones o reserva natural insignia del destino. El recorrido se realiza con un guía pedagógico exclusivo que amenizará las caminatas "
        "por senderos planos de baja dificultad organizando dinámicas de grupo, juegos ecológicos e historias educativas sobre la fauna local para niños. "
        "Almuerzo buffet incluido en restaurantes aliados dentro de las instalaciones del parque. Retorno al hotel a descansar al finalizar la tarde.\n"
        "Día 3: Talleres Culturales Colectivos y Desafíos Recreativos. Mañana interactiva dedicada a un taller artesanal familiar de pintura, cerámica "
        "o preparación guiada de postres tradicionales locales, fomentando la unión y el aprendizaje lúdico intergeneracional. Después del almuerzo, "
        "se dará inicio a una gran gymkana recreativa familiar en las zonas verdes del complejo hotelero, con retos de destreza, búsqueda del tesoro y "
        "premios para todos los participantes. Al anochecer, disfrutaremos de una función de cine familiar privado bajo las estrellas con pasabocas.\n"
        "Día 4: Recreación Libre, Recuerdos Imborrables y Clausura. Mañana libre para disfrutar plenamente de las piscinas de olas, toboganes acuáticos, "
        "canchas deportivas o simplemente descansar en las zonas de playa o descanso del hotel. Almuerzo de despedida tipo banquete familiar tradicional "
        "donde se compartirá un video o foto-álbum digital compilatorio con los mejores momentos capturados por nuestro fotógrafo profesional durante el viaje. "
        "Traslado coordinado de regreso hacia el punto de origen."
    ),
    "Premium": (
        "Día 1: Conserjería VIP, Exclusividad y Lujo sin Límites. Servicio de asistencia ejecutiva preferencial desde el momento de su arribo, "
        "gestionando de manera privada el reclamo de equipajes y facilitando un traslado terrestre VIP en vehículos blindados de alta gama o helicóptero. "
        "Alojamiento de ultra lujo en un resort de categoría internacional cinco estrellas o villa privada con un equipo de mayordomía privado las 24 horas. "
        "Cena de gala de bienvenida diseñada de forma exclusiva por un chef galardonado con estrellas Michelin, que consta de un menú degustación con maridaje.\n"
        "Día 2: Sobrevuelo Exclusivo y Experiencias de Alta Gama. Desayuno gourmet a la carta preparado por un chef privado en los balcones de su villa. "
        "Mañana dedicada a una experiencia aeronáutica sin igual con un sobrevuelo privado en helicóptero o avioneta chárter privada para apreciar la majestuosa "
        "geografía, costas o selvas del destino desde una perspectiva privilegiada. Desembarque directo en un club de golf o club náutico privado para "
        "disfrutar de un almuerzo marino de alta cocina. Tarde libre de compras exclusivas asistida por un personal shopper experto de la región.\n"
        "Día 3: Acceso Restringido, Inmersión Cultural Privada y Bienestar VIP. Experiencia de inmersión histórica o científica guiada por expertos, "
        "arqueólogos o curadores de museos con acceso privado exclusivo fuera del horario al público general. En la tarde, cata privada de cafés especiales "
        "de puntuación presidencial, rones añejos de colecciones limitadas o puros premium en un salón exclusivo de fumadores. Noche de bienestar holístico "
        "en un spa de ultra lujo reservado en su totalidad para el portador del paquete, con terapeutas internacionales de primer nivel.\n"
        "Día 4: Brunch de Alta Escuela, Clausura y Retorno en Primera Clase. Espectacular desayuno tipo brunch extendido de cocina fusión internacional "
        "en los jardines privados del resort. Tiempo libre para disfrutar de las instalaciones exclusivas de equitación, canchas de tenis profesionales "
        "o yate privado. Coordinación automatizada de salida tardía extrema (super late check-out), entrega de regalos de alta gama por parte de la gerencia "
        "del hotel y traslado de lujo directo hacia el vuelo privado o clase ejecutiva internacional de regreso."
    ),
    "Económico": (
        "Día 1: Conectividad Local, Autenticidad y Exploración Base. Llegada de forma autónoma al hostal boutique o posada nativa tradicional seleccionada "
        "minuciosamente por su inmejorable ubicación céntrica, altos estándares de limpieza y cálido ambiente comunitario de intercambio. "
        "Registro rápido en habitaciones compartidas o privadas optimizadas con servicios esenciales de ventilación, casilleros de seguridad y conectividad wifi. "
        "Tarde libre guiada mediante mapas digitales interactivos gratuitos para explorar a pie el casco histórico, plazas de mercado y monumentos públicos. "
        "Cena libre sugerida en los puestos callejeros tradicionales más recomendados.\n"
        "Día 2: Ecoturismo de Conservación y Movilidad Sostenible. Desayuno casero tradicional preparado por cocineras locales en el comedor común. "
        "Salida utilizando sistemas de transporte público local, colectivos o bicicletas compartidas para reducir la huella de carbono y los costos de traslado. "
        "Ruta de senderismo autoguiada o acompañados por jóvenes guías comunitarios locales mediante esquemas de aporte voluntario, visitando parques, "
        "senderos ecológicos públicos, cascadas o playas abiertas sin costo excesivo de entrada. Almuerzo tipo menú del día tradicional y económico.\n"
        "Día 3: Circuitos Culturales Gratuitos e Integración Internacional. Mañana dedicada enteramente a recorrer mercados tradicionales de artesanías, "
        "galerías de arte comunitario e iglesias históricas con ingreso gratuito o donativo libre. Almuerzo en comedores populares de alta calidad culinaria. "
        "En la tarde, caminata grupal organizada por el hostal hacia colinas, miradores urbanos o playas públicas para contemplar la puesta de sol de forma "
        "gratuita. Noche de integración cultural y musical en las zonas comunes del hostal, compartiendo anécdotas de viaje con mochileros.\n"
        "Día 4: Mercados Populares, Suvenires de Productores y Retorno. Desayuno ligero en la barra comunitaria. Mañana libre destinada a visitar plazas "
        "de mercado populares para adquirir recuerdos, café local en grano, dulces tradicionales o artesanías directamente de las manos de los productores "
        "locales a precios de coste. Almacenamiento seguro y gratuito de equipaje en la recepción del hostal durante las últimas horas del día, check-out regular "
        "y partida por medios propios utilizando transportes terrestres o conexiones de bajo coste."
    )
}

COMENTARIOS_POOL = {
    "Aventura": [
        "Una descarga de adrenalina total de principio a fin. Los guías demostraron un conocimiento técnico impecable en alpinismo y rescate fluvial. Los equipos como arneses, cuerdas y cascos estaban en perfecto estado de mantenimiento. El senderismo del segundo día fue verdaderamente exigente a nivel físico y aeróbico, pero coronar el mirador al amanecer compensó absolutamente todo el sudor. Lo recomiendo solo si tienes un estado físico aceptable y te gusta la aventura real sin lujos artificiales.",
        "El itinerario técnico se cumplió al pie de la letra sin retrasos logísticos. El descenso en balsa por los rápidos clase IV fue una experiencia salvaje y electrizante que puso a prueba nuestro trabajo en equipo. Dormir en carpas de alta montaña en medio de la naturaleza profunda nos desconectó del estrés del trabajo. La comida de campaña provista fue sorprendentemente rica y balanceada para darnos energía. Vale completamente la pena pagar cada peso por este nivel de organización y seguridad.",
        "Una experiencia rústica, salvaje e inolvidable en un entorno geográfico imponente. No es un plan apto para personas que busquen comodidades de hotel ni lujos. La espeleología en las cavernas subterráneas fue una actividad mística que me sacó por completo de mi zona de confort debido a la oscuridad y el agua fría, pero los guías certificados transmitían total seguridad. Recomiendo llevar calzado técnico de repuesto con excelente agarre y ropa de secado rápido."
    ],
    "Romántico": [
        "El hotel boutique superó con creces todas nuestras altas expectativas decorativas y de servicio. Nos recibieron con detalles hermosos e íntimos como pétalos de rosas frescas esparcidos por la suite, copas de champaña premium y velas aromáticas que creaban una atmósfera mágica. La cena privada de cuatro tiempos a la luz de las velas en la terraza exclusiva con violines en vivo fue un momento cinematográfico inolvidable. Es el plan definitivo si deseas celebrar un aniversario especial o una luna de miel.",
        "Buscábamos tranquilidad absoluta, privacidad y reconexión en pareja, y este paquete nos brindó exactamente ese entorno idílico. El picnic premium en medio del santuario natural estuvo perfectamente organizado; los quesos madurados y el vino tinto seleccionado eran de excelente calidad culinaria. Todo el personal del hotel fue extremadamente discreto y respetuoso con nuestra privacidad. Una escapada romántica de ensueño que repetiremos sin dudarlo el próximo año.",
        "Es un viaje mágico e ideal para parejas que busquen un escape de la rutina urbana. El circuito de spa con hidroterapia y el masaje relajante simultáneo con aceites esenciales de aromaterapia de 90 minutos nos dejó renovados por completo. Ver la puesta de sol desde el velero privado con copas de vino espumoso fue una experiencia sublime que guardaremos para siempre en el corazón. La atención personalizada al detalle justifica la inversión."
    ],
    "Familiar": [
        "Mis hijos pequeños quedaron fascinados con todas las actividades recreativas programadas y las piscinas de olas, mientras que los abuelos pudieron descansar cómodamente gracias a los accesos sencillos. La minivan ejecutiva privada para los traslados familiares era muy espaciosa, limpia y segura, con sillas especiales para los niños. El hotel contaba con un menú infantil variado y saludable. Una organización logística impecable que eliminó por completo el estrés de viajar en grupo.",
        "Excelente planificación del tiempo y los itinerarios diarios. Los recorridos en los parques temáticos y reservas ecológicas naturales están muy bien calculados en distancias cortas y senderos planos para no agotar físicamente a los niños pequeños ni a los adultos mayores. El guía pedagógico a cargo demostró una paciencia increíble con los menores, organizando juegos interactivos, trivias y dinámicas educativas de conservación ambiental muy divertidas. Volveremos en las próximas vacaciones familiares.",
        "Este viaje ofrece un balance perfecto entre la diversión interactiva para los niños y espacios de relajación real para los padres de familia. Los talleres artesanales de pintura y cerámica comunitaria donde creamos manualidades juntos fueron muy enriquecedores y unieron mucho al grupo. La función nocturna de cine bajo las estrellas con pasabocas fue el cierre ideal para un viaje inolvidable. El detalle final del foto-álbum impreso de alta resolución con las mejores tomas del viaje fue un regalo maravilloso."
    ],
    "Premium": [
        "Un servicio de conserjería VIP impecable y de primerísimo nivel internacional desde el minuto uno. Los traslados privados en vehículos blindados de alta gama y el servicio de mayordomía personalizado las 24 horas del día te hacen sentir en un oasis de exclusividad total. El menú degustación de gala diseñado por el chef Michelin maridado con vinos importados de colección fue una experiencia gastronómica multisensorial soberbia. Sin filas, sin esperas y con accesos restringidos privilegiados en todas las atracciones del destino.",
        "El paquete vale absolutamente cada centavo invertido si eres un viajero exigente que prioriza la exclusividad y el confort absoluto. El sobrevuelo privado en helicóptero chárter para apreciar los paisajes geográficos y costas desde el aire fue una experiencia majestuosa e inigualable con vistas de locura. Las instalaciones del resort de cinco estrellas contaban con amenidades de ultra lujo y campos de golf privados inmaculados. La asistencia del personal shopper facilitó la compra de obras de arte locales exclusivas.",
        "Una experiencia VIP excepcional, sofisticada y con un nivel de privacidad absoluto inigualable. La cata privada de cafés especiales con alta puntuación de taza y rones añejos limitados dictada por un sommelier experto fue sumamente educativa y placentera. El spa de ultra lujo reservado en su totalidad para nosotros nos brindó un tratamiento terapéutico de clase mundial. La gestión del check-out tardío extendido nos permitió disfrutar del resort hasta el último segundo con total comodidad."
    ],
    "Económico": [
        "Una excelente e insuperable relación calidad-precio para viajeros mochileros o con presupuestos ajustados. El hostal boutique seleccionado estaba impecablemente limpio, con sábanas frescas, casilleros seguros y una ubicación central envidiable que nos permitió ahorrar mucho dinero en transporte. Las guías digitales y mapas interactivos gratuitos provistos por la recepción fueron de gran utilidad para recorrer el centro histórico a nuestro propio ritmo. Los desayunos caseros tradicionales eran deliciosos, abundantes y llenos de sabor local.",
        "La mejor opción inteligente para conocer destinos maravillosos de forma auténtica, sostenible y económica sin gastar fortunas. El uso de transportes colectivos locales guiados por el coordinador del hostal no solo abarató drásticamente los costos de traslado, sino que nos permitió integrarnos y vivir de cerca la cotidianidad real de la población local. Las caminatas ecológicas grupales hacia las playas públicas y miradores naturales gratuitos fueron espectaculares y muy divertidas. Cumple perfectamente con todo lo prometido.",
        "Un viaje enfocado en la autenticidad, el intercambio cultural y el ahorro inteligente. Las zonas comunes del hostal propiciaron noches de integración fantásticas donde compartimos experiencias de viaje y cenas comunitarias con mochileros de múltiples nacionalidades del mundo. Comprar los suvenires, café en grano y dulces directamente en las plazas de mercado recomendadas a productores locales nos garantizó precios de coste justos y ayudó a la economía local. El almacenamiento gratuito de equipaje el último día fue un gran acierto."
    ]
}

async def main() -> None:
    print("Iniciando conexión a MongoDB...")
    await mongo.connect()
    db = mongo.database

    print("Limpiando colecciones viejas...")
    await db.destino.delete_many({})
    await db.paqueteTuristico.delete_many({})
    await db.resena.delete_many({})
    await db.multimedia.delete_many({})

    destinos_insertados = []
    multimedia_insertada = []
    paquetes_insertados = []
    resenas_insertadas = []

    print(f"Insertando {len(DESTINOS_DATA)} destinos densamente poblados...")
    for d in DESTINOS_DATA:
        d["creado_en"] = utc_now()
        res = await db.destino.insert_one(d)
        d["_id"] = res.inserted_id
        destinos_insertados.append(d)

    destinos_por_nombre = {dest["nombre"]: dest for dest in destinos_insertados}
    imagenes_por_destino: dict[str, list] = {}
    for nombre_destino, image_path in iter_destination_images():
        imagenes_por_destino.setdefault(nombre_destino, []).append(image_path)

    print("Generando multimedia desde imagenes locales reales...")
    for nombre_destino, image_paths in imagenes_por_destino.items():
        dest = destinos_por_nombre.get(nombre_destino)
        if dest is None:
            print(f"Destino sin registro en MongoDB, omitido: {nombre_destino}")
            continue
        for index, image_path in enumerate(image_paths, start=1):
            multimedia_insertada.append(build_multimedia_document(dest, image_path, index))

    print("Generando 5 paquetes enriquecidos y masivos por cada destino (Total: 100)...")
    for dest in destinos_insertados:
        for tipo in TIPOS_PAQUETE:
            servicios = ["Hospedaje especializado", "Seguro médico de cobertura amplia", "Asistencia en el destino 24/7"]
            if tipo == "Aventura":
                servicios += ["Guía de alta montaña certificado", "Equipos de protección homologados", "Transporte logístico 4x4 off-road", "Alimentación de campaña calórica"]
                precio = random.randint(850000, 1600000)
            elif tipo == "Romántico":
                servicios += ["Cena gourmet privada a la luz de las velas", "Botella de vino reserva de bienvenida", "Acceso premium al circuito de Spa", "Decoración floral en la suite"]
                precio = random.randint(1250000, 2700000)
            elif tipo == "Familiar":
                servicios += ["Entradas completas a parques temáticos", "Guía recreativo pedagógico", "Desayuno buffet tipo americano libre", "Minivan privada climatizada"]
                precio = random.randint(1600000, 3600000)
            elif tipo == "Premium":
                servicios += ["Hoteles de ultra lujo 5* Gran Selección", "Transporte privado VIP en vehículos de alta gama", "Catas exclusivas de café y rones", "Servicio de mayordomía 24h"]
                precio = random.randint(3200000, 6500000)
            else:
                servicios += ["Habitación comunitaria/privada optimizada", "Recorrido urbano a pie guiado", "Mapas digitales y guías de viaje autónomo", "Uso de cocinas e instalaciones comunes"]
                precio = random.randint(320000, 750000)

            itinerario_base = ITINERARIOS_POOL[tipo]
            descripcion_larga = f"Itinerario completo y detallado paso a paso para explorar y descubrir la magia de {dest['nombre']}:\n{itinerario_base}"

            paquete = {
                "destino_id": dest["_id"],
                "titulo": f"Plan Turístico de {tipo} Especial en {dest['nombre']}",
                "descripcion": f"Disfruta de una experiencia única, inmersiva y minuciosamente diseñada de tipo {tipo.lower()} en el destino de {dest['nombre']}. {dest['descripcion']}",
                "descripcion_larga": descripcion_larga,
                "precio": precio,
                "duracion_dias": 4,
                "tipo": tipo,
                "servicios_incluidos": servicios,
                "creado_en": utc_now()
            }
            
            res_paquete = await db.paqueteTuristico.insert_one(paquete)
            paquete_id = res_paquete.inserted_id
            paquete["_id"] = paquete_id
            paquetes_insertados.append(paquete)

            num_resenas = random.randint(2, 3)
            comentarios_disponibles = COMENTARIOS_POOL[tipo].copy()
            random.shuffle(comentarios_disponibles)

            for j in range(num_resenas):
                puntuacion = random.choice([4, 5]) if tipo in ["Premium", "Romántico"] else random.choice([3, 4, 5])
                resenas_insertadas.append({
                    "paquete_id": paquete_id,
                    "puntuacion": puntuacion,
                    "comentario": comentarios_disponibles[j % len(comentarios_disponibles)],
                    "creado_en": utc_now()
                })

    print(f"Insertando {len(multimedia_insertada)} registros detallados de multimedia...")
    await db.multimedia.insert_many(multimedia_insertada)

    print(f"Insertando {len(resenas_insertadas)} reseñas realistas y extensas...")
    await db.resena.insert_many(resenas_insertadas)

    print("\n--- ¡DATASET ALTAMENTE DENSO Y POBLADO GENERADO CON ÉXITO! ---")
    await mongo.close()

if __name__ == "__main__":
    asyncio.run(main())
