<!--
BORRADOR generado a partir de los hechos de la sesión. Antes de entregar,
reescríbelo con tu voz: agrega qué te sorprendió a ti, qué habrías hecho
distinto y qué revisaste tú personalmente. Borra este comentario al terminar.
-->

# Reflexión final

## ¿Qué tan útil fue Claude Code?

Fue muy útil para el trabajo mecánico y para explorar: en minutos tenía el mapa
del proyecto, la lista de *code smells* con su ubicación y un plan ordenado por
riesgo. Además verificó más allá de lo que pedía el reto: una comparación automática del menú original contra el
nuevo con la misma entrada, una prueba diferencial con 14 000 casos aleatorios
para `mas_vendidos` y `mypy --strict` para que los type hints no fueran
decorativos.

## ¿Qué detectó que yo no había notado?

Lo más valioso del diagnóstico fue que **la suite original era débil**. Pasa
en verde aunque cambie el texto del ticket, los mensajes de error o el orden
de los empates. Sin ese hallazgo habría refactorizado confiando en 20 tests
que no protegían lo suficiente. Escribir primero 43 pruebas de caracterización
contra el código original fue la decisión que más pagó: en R11 un error que
borraba todos los mensajes de error pasó la suite original 20/20 y solo lo
atraparon las pruebas nuevas. También encontró un bug real que la consigna no
mencionaba: cargar un JSON sin la llave `"ventas"` vaciaba el inventario antes
de tronar.

## ¿Dónde hubo que corregir o rechazar?

- **R4:** `if not codigo` parece una simplificación inocente, pero cambia el
  caso del código `0`. Pasó todos los tests; se detectó revisando el diff.
- **R9:** `Counter.most_common(n)` era la opción idiomática, pero no es
  equivalente con `n` negativo.
- **R11:** un reemplazo masivo con regex quitó también el `global` que sí hacía
  falta.

En los tres casos el patrón fue el mismo: **"simplificar" e "idiomático"
invitan a cambios que parecen equivalentes y no lo son en los bordes.**

## ¿Qué aprendí sobre refactorizar con IA?

1. **Primero la red de seguridad, después los cambios.** Los tests de
   caracterización valen más que cualquier prompt bien escrito.
2. **El prompt debe incluir la restricción y el criterio de verificación**,
   no solo el objetivo: "conserva la semántica exacta", "la salida no debe
   cambiar ni un carácter", "verifica con mypy --strict".
3. **`CLAUDE.md` funciona como contrato.** Dejar por escrito la API que
   usan los tests, las reglas de negocio y "una refactorización por commit"
   evitó que el agente renombrara `agregarProducto` o mezclara cambios.
4. **Que los tests pasen no prueba que el cambio sea correcto.** Prueba
   que no rompiste *lo que los tests miran*. La revisión del diff sigue siendo
   responsabilidad humana.
5. **Commits pequeños** hicieron que cada error fuera barato de encontrar y
   de corregir. El propio agente se equivocó al armar el commit base (solo
   incluía `.gitignore`); se notó porque el diff de R1 traía archivos
   completos y se reconstruyó la historia antes de seguir.

## ¿Qué ajustaría?

- Pedir pruebas de caracterización también para `main.py` como tests de pytest
  con `monkeypatch` de `input`, en lugar de un script externo de comparación.
- Eliminar el estado global por completo (una clase `Tienda`), negociando antes
  si se puede ajustar el contrato de los tests.
- Agregar `mypy` y `ruff format --check` a la configuración del proyecto para
  que no dependan de que alguien se acuerde de correrlos.
