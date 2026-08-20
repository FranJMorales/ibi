# Despliegue y redirecciones

## Cómo se publica el sitio

El sitio se sirve desde **Vercel** (cabecera `server: Vercel`), no desde GitHub Pages.

- **La rama `main` es producción.** Lo que se fusiona en `main` aparece en
  `https://tasasmunicipales.info`.
- **Cualquier otra rama genera solo una vista previa.** Si un pull request apunta a una
  rama intermedia en lugar de a `main`, al fusionarlo el cambio se queda en la vista
  previa y **no llega a la web real**. Es lo que ocurrió con el PR #11, cuya base era
  `feat/territory-pillars`.

Regla práctica: **todo pull request debe tener `main` como rama base.** Si se apilan
pull requests, hay que fusionarlos en orden y comprobar que el último acaba en `main`.

## Redirecciones 301 reales

Vercel aplica redirecciones en el borde a partir de `vercel.json`, así que **no hace
falta Cloudflare ni meta refresh** para tener 301 de verdad.

`vercel.json` se genera automáticamente:

```bash
python3 scripts/build_vercel_config.py     # lee redirects-301.csv y escribe vercel.json
```

Cubre 27 URLs (54 reglas, con y sin barra final):

- **25 URLs antiguas** del tipo `/{ccaa}/{provincia}/{municipio}/{tema}-{municipio}/`
  que se eliminaron en un rebuild anterior, siguen indexadas y devolvían 404. Redirigen
  a la ficha del municipio.
- **2 URLs mal asignadas de provincia**: Villarrobledo (estaba en Ciudad Real, es de
  Albacete) y Lalín (estaba en Ourense, es de Pontevedra).

Las páginas de redirección de cliente (`canonical` + `meta refresh` + `location.replace`)
se mantienen en el repositorio como respaldo: con el 301 activo, Vercel responde antes de
llegar a ellas, y si algún día se cambia de hosting seguirán funcionando.

## Sitemap

`sitemap.xml` **no se edita a mano**. Se regenera:

```bash
python3 scripts/build_sitemap.py           # regenera
python3 scripts/build_sitemap.py --check   # comprueba si está al día
```

Excluye automáticamente las páginas de redirección y las marcadas con `noindex`
(aviso legal, cookies y privacidad), y toma el `lastmod` de la fecha del último commit
que tocó cada fichero, de modo que el resultado es reproducible.

**Si aparece un conflicto de fusión en `sitemap.xml`**, no hay que resolverlo línea a
línea: acepta cualquiera de las dos versiones, ejecuta el generador y haz commit del
resultado.

```bash
git checkout --theirs sitemap.xml   # o --ours, es indiferente
python3 scripts/build_sitemap.py
git add sitemap.xml
```

## Después de publicar

1. Comprobar que el cambio está en producción, no solo en la vista previa. Por ejemplo,
   el tipo de IBI de Ourense debe ser **0,45%**:
   ```bash
   curl -s https://tasasmunicipales.info/galicia/ourense/ourense/ | grep -o 'IBI urbano.\{0,60\}'
   ```
2. Comprobar que una URL antigua devuelve 301 y no 200:
   ```bash
   curl -sI https://tasasmunicipales.info/galicia/a-coruna/ferrol/plusvalia-municipal-ferrol/ | head -3
   ```
3. En Search Console: reenviar el sitemap y pedir la reindexación de las páginas con más
   tráfico.
