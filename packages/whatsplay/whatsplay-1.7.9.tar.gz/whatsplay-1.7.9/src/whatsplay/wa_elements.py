"""
Utilities for interacting with WhatsApp Web elements
"""

import asyncio
from typing import Optional, List, Dict, Any
from playwright.async_api import (
    Page,
    ElementHandle,
    TimeoutError as PlaywrightTimeoutError,
)
import re

from .constants import locator as loc
from .constants.states import State
from .filters import MessageFilter


class WhatsAppElements:
    """Helper class for interacting with WhatsApp Web elements"""

    def __init__(self, page: Page):
        self.page = page

    async def get_state(self) -> Optional[State]:
        """
        Determina el estado actual de WhatsApp Web basado en los elementos visibles
        """
        try:
            # Checkear en orden de prioridad
            if await self.page.locator(loc.LOGGED_IN).is_visible():
                print("LOGGED_IN")
                return State.LOGGED_IN
            elif await self.page.locator(loc.LOADING).is_visible():
                print("LOADING")
                return State.LOADING
            elif await self.page.locator(loc.QR_CODE).is_visible():
                print("QR_AUTH")
                return State.QR_AUTH
            elif await self.page.locator(loc.AUTH).is_visible():
                print("AUTH")
                return State.AUTH
            elif await self.page.locator(loc.LOADING_CHATS).is_visible():
                print("LOADING_CHATS")
                return State.LOADING
            return None
        except Exception:
            return None

    async def wait_for_selector(
        self, selector: str, timeout: int = 5000, state: str = "visible"
    ) -> Optional[ElementHandle]:
        """
        Espera por un elemento y lo retorna cuando está disponible
        """
        try:
            element = await self.page.wait_for_selector(
                selector, timeout=timeout, state=state
            )
            return element
        except PlaywrightTimeoutError:
            return None

    async def click_search_button(self) -> bool:
        """Intenta hacer click en el botón de búsqueda usando múltiples estrategias"""
        try:
            # Intentar con cada selector del botón de búsqueda
            for selector in loc.SEARCH_BUTTON:
                try:
                    element = await self.page.wait_for_selector(
                        selector, timeout=1000, state="visible"
                    )
                    if element:
                        print(f"🔎 click_search_button: clic en botón de búsqueda con selector: {selector}")
                        await element.click()
                        if await self.verify_search_active():
                            print("✅ click_search_button: búsqueda activada vía botón")
                            return True
                except Exception:
                    continue

            # Si no funcionó el clic directo, intentar con atajos de teclado
            shortcuts = ["Control+Alt+/", "Control+Alt+Slash", "Control+/", "Control+f", "/", "Slash"]
            for shortcut in shortcuts:
                try:
                    await self.page.keyboard.press("Escape")  # Limpiar estado actual
                    print(f"⌨️  click_search_button: probando atajo {shortcut}")
                    await self.page.keyboard.press(shortcut)
                    if await self.verify_search_active():
                        print(f"✅ click_search_button: búsqueda activada con atajo {shortcut}")
                        return True
                except Exception:
                    continue

            return False

        except Exception as e:
            print(f"Error clicking search button: {e}")
            return False

    async def verify_search_active(self) -> bool:
        """Verifica si la búsqueda está activa usando múltiples indicadores"""
        try:
            # Verificar si el botón de cancelar búsqueda está visible
            cancel_button = await self.wait_for_selector(
                loc.CANCEL_SEARCH, timeout=1000
            )
            if cancel_button:
                return True

            # Verificar si algún campo de búsqueda está visible
            for selector in loc.SEARCH_TEXT_BOX:
                try:
                    element = await self.page.wait_for_selector(
                        selector, timeout=1000, state="visible"
                    )
                    if element:
                        return True
                except Exception:
                    continue

            return False
        except Exception:
            return False

    async def get_qr_code(self) -> Optional[bytes]:
        """
        Obtiene la imagen del código QR si está disponible
        """
        try:
            qr_element = await self.wait_for_selector(loc.QR_CODE)
            if qr_element:
                return await qr_element.screenshot()
            return None
        except Exception:
            return None

    async def search_chats(self, query: str, close=True) -> List[Dict[str, Any]]:
        """Busca chats usando un término y retorna los resultados"""
        results = []
        try:
            # Activar búsqueda
            if not await self.click_search_button():
                return results

            # Buscar campo de texto y escribir consulta
            search_box = None
            for selector in loc.SEARCH_TEXT_BOX:
                try:
                    search_box = await self.wait_for_selector(selector, timeout=2000)
                    if search_box:
                        break
                except Exception:
                    continue

            if not search_box:
                return results

            # Escribir consulta con reintento
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    await search_box.click()
                    await search_box.fill("")
                    await search_box.type(query, delay=100)
                    break
                except Exception as e:
                    if attempt == max_attempts - 1:
                        return results

            # Esperar resultados
            results_container = await self.wait_for_selector(
                loc.SEARCH_RESULT, timeout=5000
            )
            if not results_container:
                print("No search results found")
                return results

            # Obtener y procesar resultados
            items = await self.page.locator(loc.SEARCH_ITEM).all()
            for item in items:
                text = await item.inner_text()
                if text:
                    formatted = MessageFilter.filter_search_result(text)
                    results.append(formatted)

        except Exception as e:
            print(f"Error searching chats: {e}")
        finally:
            # Cerrar búsqueda
            try:
                if close:
                    await self.page.keyboard.press("Escape")
            except:
                pass

        return results

    async def open(
        self, chat_name: str, timeout: int = 10000, force_open: bool = False
    ) -> bool:
        """
        Abre un chat por su nombre visible. Si no está en el DOM, lo busca y lo abre.
        """
        # es_numero = bool(re.fullmatch(r"\+?\d+", chat_name))

        # if es_numero or force_open:
        #     numero = chat_name.lstrip("+")
        #     url = f"https://web.whatsapp.com/send?phone={numero}"
        #     await self.page.goto(url)
        #     try:
        #         await self.page.wait_for_selector(loc.CHAT_INPUT_BOX, timeout=timeout)
        #         return True
        #     except Exception:
        #         # Si falla la navegación directa, continuamos con estrategias de búsqueda
        #         pass

        # Estrategia 1: buscar el chat directamente en la lista (exacto y luego parcial)
        exact_xpath = f"//span[@title={repr(chat_name)}]"
        contains_xpath = f"//span[contains(@title, {repr(chat_name)})]"

        try:
            chat_element = await self.page.query_selector(f"xpath={exact_xpath}")
            if not chat_element:
                chat_element = await self.page.query_selector(f"xpath={contains_xpath}")
            if chat_element:
                try:
                    await chat_element.scroll_into_view_if_needed()
                except Exception:
                    pass
                await chat_element.click()
                if await self.page.query_selector(f"xpath={exact_xpath}"):
                    print(f"✅ open: abierto por coincidencia EXACTA de título → {chat_name}")
                else:
                    print(f"✅ open: abierto por coincidencia PARCIAL de título → {chat_name}")
            else:
                print(f"🔍 Chat '{chat_name}' no visible, usando buscador...")
                # Usar método robusto que incluye atajos de teclado
                if not await self.click_search_button():
                    raise Exception("❌ No se pudo activar el buscador")

                for input_xpath in loc.SEARCH_TEXT_BOX:
                    inputs = await self.page.query_selector_all(f"xpath={input_xpath}")
                    if inputs:
                        await inputs[0].fill(chat_name)
                        print(f"⌨️  open: texto de búsqueda escrito → '{chat_name}' en {input_xpath}")
                        break
                else:
                    raise Exception("❌ Input de búsqueda no encontrado")

                # Esperar y seleccionar el mejor resultado (exacto primero)
                await self.page.wait_for_selector(loc.SEARCH_ITEM, timeout=timeout)
                items = await self.page.locator(loc.SEARCH_ITEM).all()

                best_item = None
                best_partial = None
                for item in items:
                    try:
                        text = (await item.inner_text()) or ""
                        if text.strip() == chat_name:
                            best_item = item
                            break
                        if chat_name.lower() in text.lower():
                            best_partial = best_partial or item
                    except Exception:
                        continue

                target = best_item or best_partial
                if target:
                    try:
                        await target.scroll_into_view_if_needed()
                    except Exception:
                        pass
                    await target.click()
                    print("✅ open: selección desde buscador → ", "EXACTA" if best_item else "PARCIAL")
                else:
                    # Fallback al comportamiento anterior
                    await self.page.keyboard.press("ArrowDown")
                    await self.page.keyboard.press("Enter")
                    print("↘️  open: fallback ArrowDown + Enter")
                print(f"✅ Chat '{chat_name}' abierto desde buscador.")

            await self.page.wait_for_selector(loc.CHAT_INPUT_BOX, timeout=timeout)
            return True

        except PlaywrightTimeoutError:
            print(f"❌ Timeout esperando el input del chat '{chat_name}'")
            return False
        except Exception as e:
            print(f"❌ Error al abrir el chat '{chat_name}': {e}")
            return False

    async def new_group(self, group_name: str, members: List[str]) -> Optional[ElementHandle]:
        print(f"Creating new group: {group_name} with members: {members}")
        """
        Crea un nuevo grupo con el nombre especificado
        """
        try:
            # Hacer click en el botón de nuevo chat
            new_chat_button = await self.page.wait_for_selector(
                loc.NEW_CHAT_BUTTON, timeout=5000
            )
            if new_chat_button:
                await new_chat_button.click()
            new_group_button = await self.page.wait_for_selector(
                loc.NEW_GROUP_BUTTON, timeout=5000
            )
            if new_group_button:
                await new_group_button.click()
            # Esperar al campo de nombre del grupo
            member_name_input = await self.page.wait_for_selector(
                loc.INPUT_MEMBERS_GROUP, timeout=5000
            )
            if member_name_input:
                for name in members:
                    await member_name_input.fill(name)
                    await asyncio.sleep(0.5)  # Esperar un poco entre entradas
                    await self.page.keyboard.press("Enter")
                    
            enter_arrow = await self.page.wait_for_selector(
                "xpath=//span[@data-icon='arrow-forward']", timeout=5000
            )
            if enter_arrow:
                await enter_arrow.click()
                
            input_group_name = await self.page.wait_for_selector(
                loc.ENTER_GROUP_NAME, timeout=5000
            )
            if input_group_name:
                await input_group_name.fill(group_name)
                await self.page.keyboard.press("Enter")
            


        except PlaywrightTimeoutError:
            print("Timeout while trying to create a new group")
            return None
        except Exception as e:
            print(f"Error creating new group: {e}")
            return None
            
    async def add_members_to_group(
        self, group_name: str, members: List[str]
    ) -> bool:
        """
        Agrega miembros a un grupo existente. Asume que el chat del grupo ya está abierto.
        """
        try:
            if not self.open(group_name, timeout=5000):
                print(f"❌ No se pudo abrir el grupo '{group_name}'")
                return False
            
            # 2. Hacer clic en la cabecera para abrir la info del grupo
            header = await self.page.wait_for_selector(loc.GROUP_INFO_BUTTON, timeout=5000)
            await header.click()

            # 2. Buscar y hacer clic en el botón "Add participant"
            # Usamos un selector de texto porque es más robusto
            add_participant_button = await self.page.wait_for_selector(
                loc.ADD_MEMBERS_BUTTON, timeout=5000
            )
            await add_participant_button.click()

            # 3. Agregar cada miembro
            member_input = await self.page.wait_for_selector(
                loc.INPUT_MEMBERS_GROUP, timeout=5000
            )
            for member in members:
                await member_input.fill(member)
                await asyncio.sleep(0.5)
                await self.page.keyboard.press("Enter")
                await asyncio.sleep(0.5)

            # 4. Confirmar la adición
            confirm_button = await self.page.wait_for_selector(
                loc.CONFIRM_ADD_MEMBERS_BUTTON, timeout=5000
            )
            await confirm_button.click()
            await asyncio.sleep(0.5)  # Esperar un poco para que se procese
            
            confirm_add_button = await self.page.wait_for_selector('//div[text()="Add member"]', timeout=3000)
            
            # Esperar un poco para que se procese y cerrar el panel
            await asyncio.sleep(1)
            await self.page.keyboard.press("Escape")
            return True

        except PlaywrightTimeoutError:
            print(f"Timeout al intentar agregar miembros a '{group_name}'")
            await self.page.keyboard.press("Escape") # Intentar limpiar
            return False
        except Exception as e:
            print(f"Error agregando miembros a '{group_name}': {e}")
            await self.page.keyboard.press("Escape") # Intentar limpiar
            return False
    async def del_member_group(self, group_name: str, member_name: str) -> bool:
        """
        Elimina un miembro de un grupo existente. Asume que el chat del grupo ya está abierto.
        """
        try:
            if not await self.open(group_name, timeout=5000):
                print(f"❌ No se pudo abrir el grupo '{group_name}'")
                return False

            # 1. Abrir info de grupo
            print(" 1. Esperando GROUP_INFO_BUTTON...")
            header = await self.page.wait_for_selector(loc.GROUP_INFO_BUTTON, timeout=5000)
            await header.click()

            # 2. Contenedor de info del grupo
            print(" 2. Esperando contenedor 'Group info'...")
            group_info = await self.page.wait_for_selector('div[aria-label="Group info"]', timeout=5000)
            if not group_info:
                print("❌ No se encontró el contenedor 'Group info'")
                return False

            # 3. Buscar el <span> del miembro por coincidencia parcial
            print(" 3. Buscando miembro por coincidencia parcial...")
            span_member = await group_info.evaluate_handle(
                f"""
                (container) => {{
                    const spans = Array.from(container.querySelectorAll('span[title]'));
                    return spans.find(s => s.textContent.trim().toLowerCase().includes("{member_name.lower()}")) || null;
                }}
                """
            )

            # ⚠️ Verificar si se encontró o no
            if not await span_member.evaluate("el => !!el"):
                print(f"❌ No se encontró el miembro '{member_name}'")
                return False

            # 4. Subir al contenedor general del miembro (div[role="button"])
            member_row = await span_member.evaluate_handle("el => el.closest('div[role=\"button\"]')")
            if not await member_row.evaluate("el => !!el"):
                print("⚠️ No se encontró el contenedor del miembro")
                return False

            # 5. Buscar el contenedor del status
            status_container = await member_row.evaluate_handle(
                """(row) => {
                    const divs = Array.from(row.querySelectorAll('div'));
                    return divs.find(div => {
                        const span = div.querySelector('span');
                        return span && span.getAttribute('title');
                    }) || null;
                }"""
            )
            if not await status_container.evaluate("el => !!el"):
                print("⚠️ No se encontró el contenedor del estado del miembro")
                return False

            # 6. Hover sobre el estado
            print(" 4. Hover sobre el estado...")
            await status_container.scroll_into_view_if_needed()
            await status_container.hover()
            print(f"✅ Hover sobre el estado de '{member_name}'")

            # 7. Esperar botón de menú
            print(" 5. Esperando botón ⋮ ...")
            try:
                menu_btn = await self.page.wait_for_selector(
                    'button[aria-label="Open the chat context menu"]',
                    timeout=3000
                )
                await menu_btn.click()
                print("✅ Menú contextual clickeado correctamente.")
            except Exception as e:
                print(f"❌ No se pudo hacer clic en el botón del menú: {e}")
                return False

            # 8. Clic en "Remove"
            remove_button = await self.page.wait_for_selector(loc.REMOVE_MEMBER_BUTTON, timeout=5000)
            await remove_button.click()
            await asyncio.sleep(0.5)

            # 9. Confirmar
            confirm_button = await self.page.wait_for_selector('//div[text()="Remove"]', timeout=3000)
            await confirm_button.click()
            await asyncio.sleep(0.5)

            print(f"✅ Miembro '{member_name}' eliminado de '{group_name}'.")
            return True

        except PlaywrightTimeoutError:
            print(f"⏱️ Timeout al intentar eliminar miembro de '{group_name}'")
            await self.page.keyboard.press("Escape")
            return False
        except Exception as e:
            print(f"❌ Error eliminando miembro '{member_name}' de '{group_name}': {e}")
            await self.page.keyboard.press("Escape")
            return False
