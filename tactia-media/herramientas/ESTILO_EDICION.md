# Estilo de edición de los vídeos de Borja (Tactia)

Referencias que Borja aprobó el 17 oct 2026: vídeo del editor Solazzo (TikTok @solazzox, 1:55) y el «Final edit» de @only.three3 (18 s). Borja quiere copiar esa edición **tal cual**: que parezca un creador con editor detrás y que el vídeo se disfrute. Nota de la última prueba (McDonald's «pro»): 6,5-7/10.

## Lo que hacen las referencias (observado fotograma a fotograma)

**Subtítulos cinéticos (lo más característico)**
- Palabra a palabra, blancas, sans semibold (tipo SF Pro/Helvetica), sin caja ni borde, sombra muy suave.
- No van en una línea fija: cada palabra se coloca en un sitio distinto alrededor de la cabeza y del pecho y se van **acumulando** hasta formar la frase («me / preguntan / todo / el tiempo»). Al terminar la frase se borran todas juntas.
- Entran con desenfoque y escala (de 110 % a 100 %), y la última palabra a veces se escribe letra a letra.
- Una palabra clave por frase en **gigante** y en color de marca (azul en Solazzo: «aprendí», «brutales»), a la altura del pecho, con las palabras pequeñas alrededor.
- Palabras en arco o inclinadas en momentos puntuales («cuándo / cómo»).

**Cortes a pantalla completa cada 5-8 s (aprox. el 40 % del vídeo)**
- Fondo negro puro, gris claro (#D6D6D4) o gris oscuro (#333).
- Texto pequeño y centrado que se escribe letra a letra («No fue ni de un curso»).
- Objeto 3D girando detrás del texto (portátil, libro): en nuestro caso, objetos o iconos relacionados con el tema.
- Números gigantes que entran deslizándose y se inclinan en perspectiva («0» → «01»), con una palabra enorme fantasma detrás («Bien»).
- Tarjetas tipo interfaz (rejilla de «Vídeo 1…6», logos, carrusel 3D de miniaturas).

**Texto detrás de la persona** (las dos referencias): palabra enorme entre el fondo y la persona; en @only.three3 con una mezcla de sans muy gruesa y una caligráfica amarilla con brillo («Si tu *envío*», «A la zona *Centro*», «*Especiales*»).

**Cifras y elementos que vuelan**: precios gigantes («$4,99») que entran con desenfoque de movimiento, banderas e iconos pequeños con brillo neón.

**Transiciones**: casi siempre corte seco. Al entrar o salir de una pantalla completa: desenfoque total de un fotograma a otro, zoom rápido o barrido corto. Nada de transiciones de plantilla.

**Imagen**: Solazzo, oscura y con ambiente (luces de colores al fondo); @only.three3, fondo cálido beige con la persona destacada. Planos muy limpios.

**Sonido**: hay una música de fondo continua y baja debajo de la voz (no hay ningún silencio en todo el vídeo) y efectos muy suaves en las pantallas completas. Borja pidió de momento solo su voz: preguntarle antes de añadir música o efectos.

## Cómo aplicarlo a los vídeos de Borja (herramientas)
- Base: `montar_pro6.py` (look editorial, texto detrás de la cabeza, pantallas completas `kind: "full"`, subtítulos `caption_style: "clean"`).
- Falta construir para clavar el estilo: subtítulos cinéticos acumulados y colocados alrededor de la cabeza, con la palabra gigante en azul de marca; números que entran con desenfoque de movimiento; objetos 3D en las pantallas completas; caligrafía amarilla con brillo para el texto detrás de la persona.
- **Sonido sin cortes** (corregido el 17 oct): solo se quitan las pausas de 0,45 s o más, se dejan 0,16 s de margen a cada lado y cada corte lleva un fundido de audio muy corto para que no se note. Comprobar siempre escuchando los cortes.
- Pedir siempre el archivo original del móvil (no por WhatsApp).
