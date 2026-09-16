from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from app.api.v1.raffle.services import get_raffle
from app.api.v1.sales import services
from app.api.v1.sales.schemas import SaleForm
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.core.forms import form_data, safe_next, validate_form
from app.core.templates import flash, format_number, templates
from app.models import Sale, User
from app.models.sale import MAX_NUMBER, MIN_NUMBER

router = APIRouter(tags=["sales"])


def _is_htmx(request: Request) -> bool:
    return request.headers.get("hx-request") == "true"


def _redirect(request: Request, url: str) -> Response:
    """Redirección que funciona con y sin HTMX."""
    if _is_htmx(request):
        return Response(headers={"HX-Redirect": url})
    return RedirectResponse(url, status_code=303)


def _get_sale_or_404(db: Session, sale_id: int, user: User) -> Sale:
    sale = services.get_sale_for_user(db, sale_id, user)
    if sale is None:
        raise HTTPException(status_code=404)
    return sale


def _sale_values(sale: Sale) -> dict:
    return {
        "number": sale.number,
        "buyer_name": sale.buyer_name,
        "buyer_phone": sale.buyer_phone,
        "is_paid": sale.is_paid,
        "notes": sale.notes or "",
    }


# ---------- Nueva venta ----------

def _render_new(request: Request, db: Session, number: int, values: dict | None = None,
                errors: dict | None = None) -> HTMLResponse:
    errors = errors or {}
    context = {
        "number": number,
        "raffle": get_raffle(db),
        "values": values or {},
        "errors": errors,
        "number_taken": errors.get("number") == services.NUMBER_TAKEN,
        "in_sheet": _is_htmx(request),
    }
    if _is_htmx(request):
        # HTMX no reemplaza contenido en respuestas 4xx, por eso los errores van con 200
        return templates.TemplateResponse(request, "sales/_sheet.html", context)
    return templates.TemplateResponse(request, "sales/new.html", context, status_code=400 if errors else 200)


@router.get("/ventas/nueva", response_class=HTMLResponse)
def new_sale(
    request: Request,
    numero: str = "",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> HTMLResponse:
    if not numero.isdigit() or not MIN_NUMBER <= int(numero) <= MAX_NUMBER:
        raise HTTPException(status_code=404)
    number = int(numero)
    errors = {"number": services.NUMBER_TAKEN} if services.is_sold(db, number) else None
    return _render_new(request, db, number, errors=errors)


@router.post("/ventas", response_class=HTMLResponse)
def create_sale(
    request: Request,
    form: dict = Depends(form_data),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    raw_number = form.get("number", "")
    if not raw_number.isdigit() or not MIN_NUMBER <= int(raw_number) <= MAX_NUMBER:
        raise HTTPException(status_code=404)

    data, errors = validate_form(SaleForm, form)
    if data is not None:
        try:
            sale = services.create_sale(db, user, data)
        except services.SaleError as exc:
            errors = {exc.field: exc.message}
        else:
            flash(request, f"Número {format_number(sale.number)} vendido a {sale.buyer_name}")
            return _redirect(request, "/numeros")

    values = {**form, "is_paid": "is_paid" in form}
    return _render_new(request, db, int(raw_number), values, errors)


# ---------- Mis ventas ----------

@router.get("/mis-ventas", response_class=HTMLResponse)
def my_sales(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> HTMLResponse:
    sales = services.list_seller_sales(db, user)
    raffle = get_raffle(db)
    return templates.TemplateResponse(
        request,
        "sales/mine.html",
        {"sales": sales, "summary": services.summarize(sales, raffle.ticket_price)},
    )


# ---------- Todas las ventas (admin) ----------

@router.get("/admin/ventas", response_class=HTMLResponse)
def all_sales(
    request: Request,
    vendedor: str = "",
    estado: str = "",
    q: str = "",
    orden: str = "",
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> HTMLResponse:
    filters = services.SaleFilters.from_params(vendedor, estado, q, orden)
    sales = services.list_sales(db, filters)
    raffle = get_raffle(db)
    return templates.TemplateResponse(
        request,
        "sales/admin_list.html",
        {
            "sales": sales,
            "filters": filters,
            "summary": services.summarize(sales, raffle.ticket_price),
            "seller_options": [("", "Todos")] + [(u.id, u.full_name) for u in services.list_sellers(db)],
            "current_url": str(request.url.path) + (f"?{request.url.query}" if request.url.query else ""),
        },
    )


# ---------- Editar / eliminar ----------

def _render_edit(request: Request, db: Session, sale: Sale, values: dict, next_url: str,
                 errors: dict | None = None, status_code: int = 200) -> HTMLResponse:
    numbers = sorted({*services.available_numbers(db), sale.number})
    return templates.TemplateResponse(
        request,
        "sales/edit.html",
        {
            "sale": sale,
            "values": values,
            "errors": errors or {},
            "next": next_url,
            "number_options": [(n, format_number(n)) for n in numbers],
        },
        status_code=status_code,
    )


@router.get("/ventas/{sale_id}/editar", response_class=HTMLResponse)
def edit_sale_page(
    sale_id: int,
    request: Request,
    next: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> HTMLResponse:
    sale = _get_sale_or_404(db, sale_id, user)
    return _render_edit(request, db, sale, _sale_values(sale), safe_next(next, "/mis-ventas"))


@router.post("/ventas/{sale_id}/editar", response_class=HTMLResponse)
def update_sale(
    sale_id: int,
    request: Request,
    form: dict = Depends(form_data),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    sale = _get_sale_or_404(db, sale_id, user)
    next_url = safe_next(form.get("next"), "/mis-ventas")

    data, errors = validate_form(SaleForm, form)
    if data is not None:
        try:
            services.update_sale(db, sale, data)
        except services.SaleError as exc:
            errors = {exc.field: exc.message}
            db.refresh(sale)
        else:
            flash(request, f"Venta del número {format_number(sale.number)} actualizada")
            return RedirectResponse(next_url, status_code=303)

    values = {**form, "is_paid": "is_paid" in form}
    return _render_edit(request, db, sale, values, next_url, errors, status_code=400)


@router.post("/ventas/{sale_id}/pagado", response_class=HTMLResponse)
def toggle_paid(
    sale_id: int,
    request: Request,
    form: dict = Depends(form_data),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    sale = _get_sale_or_404(db, sale_id, user)
    services.toggle_paid(db, sale)
    if _is_htmx(request):
        return templates.TemplateResponse(request, "sales/_sale_item.html", {"sale": sale})
    return RedirectResponse(safe_next(form.get("next"), "/mis-ventas"), status_code=303)


@router.post("/ventas/{sale_id}/eliminar")
def delete_sale(
    sale_id: int,
    request: Request,
    form: dict = Depends(form_data),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    sale = _get_sale_or_404(db, sale_id, user)
    number = sale.number
    services.delete_sale(db, sale)
    flash(request, f"Venta del número {format_number(number)} eliminada. El número quedó disponible.")
    return RedirectResponse(safe_next(form.get("next"), "/mis-ventas"), status_code=303)
