from django.forms.widgets import media_property, Media
from django.template import loader
from django.templatetags.static import static
from django.utils.functional import lazy


class Mediasaate:
  '''
  Lisää kuhunkin periytettyyn luokkaan tarvittaessa `media`-määreen.
  '''
  def __init_subclass__(cls, *args, **kwargs):
    super().__init_subclass__(*args, **kwargs)
    if 'media' not in vars(cls):
      cls.media = media_property(cls)


class Media(Media):
  '''
  Täydennetty `Media`-toteutus, joka ottaa parametreinä ja tuottaa tulosteena
  (__html__()) pelkän polun lisäksi elementille tarvittavat HTML-määreet.

  Tuloste on muotoa `<{link,script} attr="attr" ...></...>`.

  Alustus ottaa parametrin `polku`: suhteellinen viittaus `static`-hakemistoon
  tai absoluuttinen, `http(s)://`-alkuinen viittaus.

  Muut, nimetyt parametrit tulkitaan HTML-määreinä.

  Kaksi Media-oliota tulkitaan samaksi puhtaasti niiden viittaman `polun`
  perusteella. Tällä on merkitystä periytyshierarkian yhdessä käyttämää
  mediaa muodostettaessa.
  '''
  # pylint: disable=function-redefined
  attrs: dict
  leima: list

  def __init__(self, polku, **kwargs):
    super().__init__()
    self.polku = polku
    self.kwargs = kwargs
    # def __init__

  def __hash__(self):
    return hash(self.polku)
    # def __hash__

  def __eq__(self, toinen):
    return isinstance(toinen, type(self)) \
    and self.polku == toinen.polku
    # def __eq__

  def __html__(self):
    return loader.render_to_string(
      'django/forms/attrs.html',
      {'attrs': self.attrs},
    ).join(self.leima)
    # def __html__

  # class Media


class JSMedia(Media):
  ''' Komentosarja + määreet. '''
  leima = ('<script ', '></script>')

  @property
  def attrs(self):
    return {
      'src': self.absolute_path(self.polku),
      **self.kwargs,
    }

  # class JSMedia


class CSSMedia(Media):
  ''' Asettelutiedosto + määreet. '''
  leima = ('<link ', '/>')

  @property
  def attrs(self):
    return {
      'href': self.absolute_path(self.polku),
      'rel': 'stylesheet',
      **self.kwargs,
    }

  # class CSSMedia


class JSModuuli(JSMedia):
  ''' Komentosarja tyyppiä `<script type="module" src="...">`. '''

  @property
  def attrs(self):
    return {
      **super().attrs,
      'type': 'module',
    }
    # def attrs

  # class JSModuuli


class JSBool(int):
  '''
  Javascript-totuusarvo. Esiintyy JSON-datassa paljaana arvona
  `true` tai `false`.
  '''
  def __repr__(self):
    return repr(bool(self)).lower()
    # def __repr__

  # class JSBool


def lazy_static(media):
  ''' Poimi static-mediatiedoston lopullinen URL ajonaikaisesti. '''
  return lazy(static, str)(media)
