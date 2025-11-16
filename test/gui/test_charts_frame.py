"""
GUI tests for ChartsFrame (dashboard).

This module exercises the dashboard behavior with various mocked scenarios:

- User not logged in: placeholder message instead of charts.
- No data: 'no data available' style fallback in the container.
- Full data path using a fake matplotlib backend (no real plotting dependency).
- Behavior when matplotlib imports fail (textual fallback, no crash).
- Categories API failure: warning path while still rendering some content.

Assertions focus on widget presence and robustness, not visual correctness.
"""

import pytest
import tkinter as tk
from unittest.mock import MagicMock

def test_charts_user_not_logged_in(app, mock_api):
    """Utente non loggato -> container mostra messaggio di login richiesto."""
    frame = app.frames['ChartsFrame']
    app.user_id = None
    frame.refresh()
    # Placeholder presente (>=1 widget)
    assert len(frame.charts_container.winfo_children()) >= 1

def test_charts_no_data(logged_in_app, mock_api):
    """Nessun dato da API -> messaggio 'No data available'."""
    app = logged_in_app
    frame = app.frames['ChartsFrame']
    mock_api['get_categories'].return_value = {'success': True, 'data': []}
    mock_api['get_expenses'].return_value = {'success': True, 'data': []}
    mock_api['get_balance_breakdown_charts'].return_value = {'success': True, 'data': {}}
    frame.refresh()
    assert len(frame.charts_container.winfo_children()) >= 1

def test_charts_with_data(logged_in_app, mock_api, monkeypatch):
    """Rendering con dati -> mock matplotlib per evitare dipendenza reale."""
    app = logged_in_app
    frame = app.frames['ChartsFrame']
    mock_api['get_categories'].return_value = {'success': True, 'data': [{'id': 1, 'name': 'Food'}]}
    mock_api['get_expenses'].return_value = {'success': True, 'data': [
        {'date': '2025-01-01', 'price': 10.0, 'category_id': 1},
        {'date': '2025-01-02', 'price': 5.0, 'category_id': 1}
    ]}
    mock_api['get_balance_breakdown_charts'].return_value = {
        'success': True,
        'data': {'credits_received': 20, 'debits_sent': 5, 'credits_sent': 3,
                 'debits_received': 2, 'net': 15, 'legacy': 18}
    }

    # Mock di importlib.import_module per simulare matplotlib
    import types

    class _FakeFig:
        """
        Figura fittizia compatibile con le chiamate del codice.
        charts_frame usa:
          - fig.subplots_adjust(hspace=..., wspace=...)
          - fig.autofmt_xdate(rotation=..., ha=...)
        Le implementiamo come no-op per compatibilità.
        """
        def subplots_adjust(self, **kwargs):
            pass
        def autofmt_xdate(self, *args, **kwargs):
            pass

    class AxGrid:
        """
        Contenitore 2D che supporta indicizzazione numpy-like:
          axes[0, 0], axes[0, 1], ecc.
        Questo evita l'errore "list indices must be integers or slices, not tuple".
        """
        def __init__(self, data):
            self._data = data
        def __getitem__(self, idx):
            if isinstance(idx, tuple):
                r, c = idx
                return self._data[r][c]
            return self._data[idx]

    def _make_fake_fig_axes():
        class FakeAx:
            """
            Asse fittizio con i metodi invocati in ChartsFrame:
              - pie, set_title, axis, text, plot
              - set_ylabel
              - tick_params, grid, set_facecolor
              - bar (ritorna barre finte con get_height/get_x/get_width)
              - xaxis.set_major_formatter / set_major_locator
            Tutte le operazioni sono no-op per garantire stabilità del test.
            """
            def __init__(self):
                self.xaxis = types.SimpleNamespace(
                    set_major_formatter=lambda f: None,
                    set_major_locator=lambda f: None
                )
            def pie(self, *a, **k): pass
            def set_title(self, *a, **k): pass
            def axis(self, *a, **k): pass
            def text(self, *a, **k): pass
            def plot(self, *a, **k): pass
            def set_ylabel(self, *a, **k): pass
            def tick_params(self, *a, **k): pass
            def grid(self, *a, **k): pass
            def set_facecolor(self, *a, **k): pass
            def bar(self, *a, **k):
                class B:
                    def get_height(self): return 10
                    def get_x(self): return 0
                    def get_width(self): return 1
                return [B()]

        fig = _FakeFig()
        raw = [[FakeAx(), FakeAx()], [FakeAx(), FakeAx()]]
        axes = AxGrid(raw)
        return fig, axes

    fake_pyplot = types.SimpleNamespace(
        subplots=lambda *a, **k: _make_fake_fig_axes(),
        rcParams={},
        cm=types.SimpleNamespace(Dark2=types.SimpleNamespace(colors=['#111111', '#222222', '#333333'])),
        close=lambda fig: None
    )

    def _fake_import(name):
        if name == 'matplotlib.pyplot':
            return fake_pyplot
        elif name == 'matplotlib.dates':
            # Formatter e Locator fittizi
            return types.SimpleNamespace(DateFormatter=lambda f: None, AutoDateLocator=lambda: None)
        elif name == 'matplotlib.backends.backend_tkagg':
            class FakeCanvas:
                """
                Wrapper canvas fittizio: restituisce un vero tk.Frame come widget
                in modo che pack() aggiunga un figlio reale a charts_container.
                """
                def __init__(self, fig, master=None):
                    self._w = tk.Frame(master)
                def get_tk_widget(self): return self._w
                def draw(self): pass
            return types.SimpleNamespace(FigureCanvasTkAgg=FakeCanvas)
        raise ImportError(name)

    # Sostituiamo gli import di matplotlib con i finti
    monkeypatch.setattr('importlib.import_module', _fake_import)

    # Act
    frame.refresh()

    # Assert: almeno un widget (canvas) creato dentro charts_container
    assert len(frame.charts_container.winfo_children()) >= 1

def test_charts_matplotlib_missing(logged_in_app, mock_api, monkeypatch):
    """Import matplotlib fallisce -> fallback testuale senza eccezioni."""
    app = logged_in_app
    frame = app.frames['ChartsFrame']
    mock_api['get_categories'].return_value = {'success': True, 'data': []}
    mock_api['get_expenses'].return_value = {'success': True, 'data': []}
    mock_api['get_balance_breakdown_charts'].return_value = {'success': True, 'data': {}}

    # Forziamo l'assenza di matplotlib
    monkeypatch.setattr('importlib.import_module', lambda name: (_ for _ in ()).throw(ImportError("No matplotlib")))

    frame.refresh()
    # Verifica che il fallback (label testuale) sia stato creato
    assert len(frame.charts_container.winfo_children()) >= 1

def test_charts_categories_error(logged_in_app, mock_api):
    """Errore caricamento categorie -> warning interno, prosegue con altri dataset."""
    app = logged_in_app
    frame = app.frames['ChartsFrame']
    mock_api['get_categories'].return_value = {'success': False, 'error': 'fail'}
    mock_api['get_expenses'].return_value = {'success': True, 'data': []}
    mock_api['get_balance_breakdown_charts'].return_value = {'success': True, 'data': {}}
    frame.refresh()
    # Il container viene comunque popolato con messaggi di fallback
    assert len(frame.charts_container.winfo_children()) >= 1