# Estilo de edición de los vídeos de Borja (Tactia)

Referencias que Borja aprobó el 17 oct 2026: vídeo del editor Solazzo (TikTok @solazzox, 1:55) y el «Final edit» de @only.three3 (18 s). Borja quiere copiar esa edición **tal cual**: que parezca un creador con editor detrás y que el vídeo se disfrute. Nota de la última prueba (McDonald's «pro»): 6,5-7/10.


## REFERENCIA PRINCIPAL (17 oct, 15:49): Daniel Gallo (@danielgalloq) · «No te vuelvas a memorizar tus guiones» (33 s)
Borja: «voy a empezar a hacer esto». Este es el estilo que manda a partir de ahora.

- **Ritmo**: 17 cortes en 33 s. Al principio un corte cada 0,5-1 s; luego cada 2-4 s. Nunca más de 4 s en el mismo plano.
- **Mucho B-roll grabado por él mismo** (más de la mitad del vídeo): escribiendo en el teclado, sentado al escritorio con luz LED azul verdosa, con la cabeza entre las manos, con el portátil bajo un flexo, pensando frente a una pizarra, en el gimnasio, tumbado en la cama. Planos oscuros, cinematográficos, con luces prácticas (LED, lámpara) y sin mirar a cámara. Cada plano ilustra literalmente la frase que dice.
- **Plano principal**: él a cámara con micro de mano, fondo oscuro con luces cálidas y un LED, varios encuadres (primer plano y plano medio, incluso de días distintos).
- **Subtítulos**: UNA palabra cada vez (dos como mucho), sans gruesa blanca, en el centro de la pantalla; cambian al ritmo de la voz. En algunos planos la palabra toma el color de la escena (azul verdoso).
- **Gancho**: composición tipográfica que se construye palabra a palabra encima de él: «No te» grande y gruesa, «vuelvas» pequeña, «a memorizar» en cursiva serif amarilla, «tus» pequeña, «guiones» en cursiva serif.
- **Pantallas completas**: fondo blanco con la palabra en verde azulado oscuro (#0B4A4F), o fondo verde azulado con letra blanca, una palabra cada vez («hasta», «pruebes», «esto», «menos»). Para los conceptos clave, cursiva serif fina y pequeña en el centro («el gancho», «el valor», «llamado a la acción»).
- **Clips en tarjeta redondeada sobre negro** (imagen dentro de la imagen) con subtítulo encima. Nosotros solo con material de Borja, nunca vídeos de otros.
- **Bloques de texto apilados** sobre el B-roll, alineados a la izquierda («divide / todo en / tres partes»).
- **Imagen**: oscura, contraste alto, sombras azul verdosas y luces cálidas.
- **Sonido**: música continua de fondo (no hay silencios). Preguntar a Borja antes de añadirla.

Para conseguirlo, Borja tiene que grabar por cada vídeo: la toma principal y entre 5 y 8 planos recurso de 3-5 s que ilustren el guion.

## ESTILO APROBADO (18 oct, Borja: «ese es los vídeos que yo quiero que hagas con todo… es la hostia») · Espía v4
- **Imagen a cámara**: su fondo tal cual (nada de luz azul ni oscurecer el fondo); sobre él, luz algo más cálida (`e.style = "warm"`: máscara de la persona, balance cálido suave, viñeta ligera, grano fino).
- **Sin fotos de banco ni iconos sueltos ni destellos** (`e.clean = True`).
- **Subtítulos** pequeños, una palabra cada vez, crema; la palabra clave en cursiva serif amarilla (`e.capstyle = "gallo"`).
- **Gancho**: frase apilada palabra a palabra sobre él, sin franja oscura (`scrim=False`), tamaños 64 / 104 / 128.
- **Partes leídas → escenas animadas de Remotion** (`remotion/tactia-video`, composición `Step` y escenas propias): título que entra palabra a palabra sincronizado con la voz + un elemento animado (móvil genérico con chat, lista que se tacha, comparativa, barras, contador, calendario, ticket, story…). Paleta oscura con brillo verde azulado/ámbar, Inter Tight + Instrument Serif. Nunca logos de marcas.
- Herramienta: `e.scene("Step", clave, desde, hasta, kicker=..., title=[[...]], widget={...})` con tiempos de origen (`e.S(clave, "palabra")`); `gallo.py` renderiza las escenas (render.mjs) y las monta como clips.
- Pantallas de palabras blanco / verde azulado de 0,5-2 s solo para frases cortas («de manera gratuita», «¿Cómo copiarlo?»).
- **Golpe de sonido de entrada (aprobado el 22 oct):** «fiuuu» + golpe suave (efecto propio, `assets/riser.wav`) y zoom al 112 % a los 0,2 s que vuelve al 100 % en 0,4 s. Solo en el primer segundo; después, solo su voz. En `gallo.py` va activado por defecto (`e.intro_sfx = False` para quitarlo).

## Lecciones de los 6 vídeos de referencia (28 oct 2026)
Borja mandó 6 vídeos para aprender a editar bien: 4 del editor Joseph (@josephvideoediting: cómo enseña a Claude a editar Reels y vídeos largos, diseño de sonido y su marca personal) y 2 de Mario (@mario.kaizen: sistema de Claude Code para hacer Reels en serie). Solo se usa lo que aprendemos; nunca su material.

**1. Planificar antes de animar (lo más importante).** Antes de tocar nada, una tabla con cada frase del guion y qué tipo de escena lleva:
- **Solo subtítulos**: Borja a cámara con texto.
- **Subtítulos + interfaz**: una tarjeta o pantallita en el tercio de abajo; el fondo detrás se oscurece y se desenfoca un poco para que se lea.
- **Media pantalla**: la animación arriba y Borja abajo, o al revés.
- **Pantalla completa**: la animación ocupa todo (las partes leídas siempre van así).
Orden de trabajo: cortes → plan → animar primero la intro → hoja con todas las escenas para revisar → resto del vídeo → sonido. Confirmar el plan con Borja si el vídeo es nuevo.

**2. Subtítulos.** En el tercio de abajo y centrados (salvo diseños especiales). Sans en blanco cálido (#F3F3F3, no blanco puro) con sombra muy suave; la palabra especial en cursiva serif del color de acento, con un brillo ligero. Entran palabra a palabra: cada palabra sube un poco desde abajo, con fundido y un desenfoque muy leve; la frase entera tarda 1,5 s como mucho. Texto más pequeño de lo normal; solo se agranda lo que tiene que llamar la atención.

**3. Los tres errores de principiante:**
- Todo demasiado grande → hacer cada elemento un 25 % más pequeño.
- Efectos por todas partes → guardarlos para lo que de verdad tiene que llamar la atención. Menos es más.
- Colores chillones (negro puro, blanco puro, rojo intenso) → colores más apagados, que se ven más profesionales.

**4. Gancho.** Pensar «¿qué es lo que hace que quieran ver el vídeo?» y enseñar eso en pantalla: la palabra del miedo, el deseo o el número («Gratis», «0 €», «Reseña de 1 estrella»), resaltada en la cursiva de acento.

**5. Composición.** Cada escena tiene un solo foco (Borja, el texto o el objeto) colocado en la zona principal, y pocos elementos de apoyo alrededor. Fondos que funcionan: blanco liso; blanco con sombra proyectada y una rejilla suave; amarillo con sombra y rejilla. Escenas con Borja: él en el centro con el gráfico apoyándole, o él a un lado y el gráfico al otro.

**6. Cortes.** Transcripción palabra a palabra y quitar cada silencio y cada toma fallida, usando el guion como referencia. Mantener nuestra regla de sonido sin cortes bruscos (ver más abajo).

**7. Sonido (pendiente del OK de Borja: de momento solo su voz y el golpe de entrada).** Cómo lo hace Joseph:
- El sonido solo subraya lo que se ve: si no pasa nada en pantalla, no suena nada.
- Tres familias: «fiuuu» para lo que se mueve (deslizar, zoom, cambio de escena); texturas para lo que aparece sin moverse (pop al salir un texto, clic de interfaz, tecleo al escribir); subidas y golpes para crear expectación (unos 5 s después del gancho, al entrar en el cuerpo del vídeo, y al cambiar de idea o de parte).
- Nunca alto y nunca por encima de la voz; un solo momento fuerte por escena; el pico del «fiuuu» en el fotograma más rápido del movimiento.
- Música solo debajo de él hablando, a unos −20 dB, nunca debajo de las animaciones.

**8. Estructura de guion que se repite en los virales** (Mario): gancho → «La realidad es esta…» → un ejemplo concreto → «Y aquí viene lo importante…» → cierre.

**9. Estilo tipo pizarra** (Mario): fondo blanco con rejilla, tarjetas de colores pastel con títulos cortos («LA SKILL», «GRATIS», «3 PARTES»), un círculo amarillo a mano alrededor de la tarjeta clave y Borja en una tarjeta redondeada en una esquina. Sirve para explicar pasos o listas. En vídeos largos, carteles grandes de capítulo («PARTE 1»).

**10. Qué formatos traen clientes** (Joseph, 120 publicaciones de 12 editores): enseñar el trabajo terminado, recursos y tutoriales, historia de cliente, opinión con animación, proceso → resultado, antes y después. Para Tactia: herramientas y tutoriales (nuestros guiones), antes y después, y proceso → resultado.

**No lo hacemos:** avatares o voces de IA (HeyGen, ElevenLabs) en lugar de Borja, copiar vídeos de otros creadores, ni vídeos de banco (Pexels) sin preguntar a Borja.

## Regla fija (17 oct, Borja)
- **Borja solo sale en pantalla cuando mira a cámara.** Todo lo que viene de las grabaciones leídas («Guion N – voz») va SIEMPRE tapado con pantallas completas (palabra a palabra en blanco / verde azulado, o gráficos del paso). Nunca se le ve leyendo.
- También dentro de las tomas a cámara: cada momento en que no mira al objetivo (detector de mirada `gaze.py` + revisión a ojo, `spec_util.away`) se tapa igual.
- Nunca solo texto: las partes leídas van con escenas animadas (ver «Estilo aprobado»); objetos 3D (Fluent Emoji 3D, licencia MIT) solo dentro de esas escenas; fotos reales solo si Borja las manda.
- Herramienta: `gallo.py` con `e.voice = {"clave de la grabación leída"}`: rellena automáticamente cualquier hueco sin pantalla.

## Lo que hacen las referencias anteriores (Solazzo y @only.three3) (observado fotograma a fotograma)

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
