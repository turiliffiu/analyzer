"""
Excel Exporter - Genera file Excel multi-sheet per analisi Ericsson
9 fogli: RadioUnits, Allarmi, FRU, PUSCH, RET, TMA, Fiber, SFP, BranchPairs
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO


# Colori intestazioni per ogni sheet
COLOR_BLUE   = "4472C4"
COLOR_RED    = "C00000"
COLOR_ORANGE = "ED7D31"
COLOR_GREEN  = "70AD47"
COLOR_PURPLE = "7030A0"
COLOR_TEAL   = "00B0F0"
COLOR_GREY   = "595959"
COLOR_GOLD   = "BF8F00"
COLOR_DARK   = "243F60"

# Colori evidenziazione valori critici
BG_CRITICAL  = "FFCCCC"  # rosso chiaro
BG_WARNING   = "FFF2CC"  # giallo chiaro
BG_NORMAL    = "E2EFDA"  # verde chiaro


class ExcelExporter:
    """Genera Excel professionale con 9 sheet formattati"""

    def __init__(self, analysis):
        self.analysis = analysis
        self.wb = Workbook()
        self.wb.remove(self.wb.active)   # rimuove sheet vuoto default

    def generate(self) -> BytesIO:
        """Genera il workbook e restituisce BytesIO"""
        self._sheet_radio_units()
        self._sheet_allarmi()
        self._sheet_fru()
        self._sheet_pusch()
        self._sheet_ret()
        self._sheet_tma()
        self._sheet_fiber()
        self._sheet_sfp()
        self._sheet_branch_pairs()

        excel_file = BytesIO()
        self.wb.save(excel_file)
        excel_file.seek(0)
        return excel_file

    # ------------------------------------------------------------------ #
    #  Utility                                                             #
    # ------------------------------------------------------------------ #

    def _header_style(self, ws, headers, color):
        """Applica stile intestazione con colore scelto"""
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF", size=10)
            cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    def _autosize(self, ws):
        """Autosize colonne in base al contenuto"""
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                try:
                    if cell.value:
                        max_len = max(max_len, len(str(cell.value)))
                except Exception:
                    pass
            ws.column_dimensions[col_letter].width = min(max_len + 4, 40)

    def _row_fill(self, ws, row_idx, color):
        """Colora una riga intera"""
        for cell in ws[row_idx]:
            cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")

    # ------------------------------------------------------------------ #
    #  1. Radio Units VSWR                                                 #
    # ------------------------------------------------------------------ #

    def _sheet_radio_units(self):
        ws = self.wb.create_sheet("Radio Units VSWR")
        headers = ['FRU', 'Board', 'RF Port', 'Branch Pair', 'TX', 'TX Unit',
                   'VSWR', 'Return Loss (dB)', 'RX (dBm)', 'VSWR Warning', 'VSWR Critical']
        self._header_style(ws, headers, COLOR_BLUE)

        for idx, unit in enumerate(self.analysis.radio_units.all(), start=2):
            row = [
                unit.fru, unit.board, unit.rf_port, unit.branch_pair,
                float(unit.tx) if unit.tx else '',
                unit.tx_unit,
                float(unit.vswr),
                float(unit.return_loss) if unit.return_loss else '',
                float(unit.rx) if unit.rx else '',
                'Sì' if unit.is_vswr_warning else 'No',
                'Sì' if unit.is_vswr_critical else 'No',
            ]
            for col, val in enumerate(row, start=1):
                ws.cell(row=idx, column=col, value=val)

            # Evidenzia righe critiche
            if unit.is_vswr_critical:
                self._row_fill(ws, idx, BG_CRITICAL)
            elif unit.is_vswr_warning:
                self._row_fill(ws, idx, BG_WARNING)

        self._autosize(ws)

    # ------------------------------------------------------------------ #
    #  2. Allarmi                                                          #
    # ------------------------------------------------------------------ #

    def _sheet_allarmi(self):
        ws = self.wb.create_sheet("Allarmi")
        headers = ['Severity', 'Alarm Number', 'Causa']
        self._header_style(ws, headers, COLOR_RED)

        SEVERITY_COLORS = {
            'CRITICAL': BG_CRITICAL,
            'MAJOR': BG_WARNING,
            'MINOR': BG_NORMAL,
        }

        for idx, alarm in enumerate(self.analysis.alarms.all(), start=2):
            ws.cell(row=idx, column=1, value=alarm.severity)
            ws.cell(row=idx, column=2, value=alarm.alarm_number)
            ws.cell(row=idx, column=3, value=alarm.cause)
            color = SEVERITY_COLORS.get(alarm.severity, '')
            if color:
                self._row_fill(ws, idx, color)

        self._autosize(ws)

    # ------------------------------------------------------------------ #
    #  3. FRU                                                              #
    # ------------------------------------------------------------------ #

    def _sheet_fru(self):
        ws = self.wb.create_sheet("FRU")
        headers = ['Nome', 'Board', 'PM Temp', 'Temperatura (°C)', 'Temp Elevata (>60°C)']
        self._header_style(ws, headers, COLOR_ORANGE)

        for idx, fru in enumerate(self.analysis.fru_units.all(), start=2):
            ws.cell(row=idx, column=1, value=fru.name)
            ws.cell(row=idx, column=2, value=fru.board)
            ws.cell(row=idx, column=3, value=fru.pmtemp)
            ws.cell(row=idx, column=4, value=fru.temp if fru.temp is not None else 'N/A')
            ws.cell(row=idx, column=5, value='Sì' if fru.is_temp_high else 'No')
            if fru.is_temp_high:
                self._row_fill(ws, idx, BG_CRITICAL)

        self._autosize(ws)

    # ------------------------------------------------------------------ #
    #  4. PUSCH / PUCCH                                                    #
    # ------------------------------------------------------------------ #

    def _sheet_pusch(self):
        ws = self.wb.create_sheet("PUSCH PUCCH RSSI")
        headers = ['Cell', 'SC', 'FRU', 'Board', 'PUSCH', 'PUCCH',
                   'Port A', 'Port B', 'Port C', 'Port D', 'Delta', 'RSSI Alto']
        self._header_style(ws, headers, COLOR_PURPLE)

        for idx, row_data in enumerate(self.analysis.pusch_data.all(), start=2):
            row = [
                row_data.cell, row_data.sc, row_data.fru, row_data.board,
                float(row_data.pusch), float(row_data.pucch),
                float(row_data.port_a) if row_data.port_a else '',
                float(row_data.port_b) if row_data.port_b else '',
                float(row_data.port_c) if row_data.port_c else '',
                float(row_data.port_d) if row_data.port_d else '',
                float(row_data.delta) if row_data.delta else '',
                'Sì' if row_data.is_rssi_high else 'No',
            ]
            for col, val in enumerate(row, start=1):
                ws.cell(row=idx, column=col, value=val)
            if row_data.is_rssi_high:
                self._row_fill(ws, idx, BG_WARNING)

        self._autosize(ws)

    # ------------------------------------------------------------------ #
    #  5. RET Devices                                                      #
    # ------------------------------------------------------------------ #

    def _sheet_ret(self):
        ws = self.wb.create_sheet("RET Devices")
        headers = ['Antenna Group', 'Antenna Near Unit', 'Radio Unit',
                   'Status', 'Device Type', 'Product Nr', 'Revision', 'Unique ID']
        self._header_style(ws, headers, COLOR_TEAL)

        for idx, ret in enumerate(self.analysis.ret_devices.all(), start=2):
            ws.cell(row=idx, column=1, value=ret.antenna_group)
            ws.cell(row=idx, column=2, value=ret.antenna_near_unit)
            ws.cell(row=idx, column=3, value=ret.radio_unit)
            ws.cell(row=idx, column=4, value=ret.status)
            ws.cell(row=idx, column=5, value=ret.device_type)
            ws.cell(row=idx, column=6, value=ret.product_nr)
            ws.cell(row=idx, column=7, value=ret.revision)
            ws.cell(row=idx, column=8, value=ret.unique_id)

        self._autosize(ws)

    # ------------------------------------------------------------------ #
    #  6. TMA Devices                                                      #
    # ------------------------------------------------------------------ #

    def _sheet_tma(self):
        ws = self.wb.create_sheet("TMA Devices")
        headers = ['Antenna Group', 'Antenna Near Unit', 'Radio Unit',
                   'Status', 'Device Type', 'Product Nr', 'Revision', 'Unique ID']
        self._header_style(ws, headers, COLOR_GREEN)

        for idx, tma in enumerate(self.analysis.tma_devices.all(), start=2):
            ws.cell(row=idx, column=1, value=tma.antenna_group)
            ws.cell(row=idx, column=2, value=tma.antenna_near_unit)
            ws.cell(row=idx, column=3, value=tma.radio_unit)
            ws.cell(row=idx, column=4, value=tma.status)
            ws.cell(row=idx, column=5, value=tma.device_type)
            ws.cell(row=idx, column=6, value=tma.product_nr)
            ws.cell(row=idx, column=7, value=tma.revision)
            ws.cell(row=idx, column=8, value=tma.unique_id)

        self._autosize(ws)

    # ------------------------------------------------------------------ #
    #  7. Fiber Links                                                       #
    # ------------------------------------------------------------------ #

    def _sheet_fiber(self):
        ws = self.wb.create_sheet("Fiber Links")
        headers = ['Link', 'FRU', 'DL Loss (dB)', 'UL Loss (dB)',
                   'DL Critico (>3.5dB)', 'UL Critico (>3.5dB)']
        self._header_style(ws, headers, COLOR_GREY)

        for idx, fiber in enumerate(self.analysis.fiber_links.all(), start=2):
            ws.cell(row=idx, column=1, value=fiber.link)
            ws.cell(row=idx, column=2, value=fiber.fru)
            ws.cell(row=idx, column=3, value=float(fiber.dl_loss) if fiber.dl_loss else '')
            ws.cell(row=idx, column=4, value=float(fiber.ul_loss) if fiber.ul_loss else '')
            ws.cell(row=idx, column=5, value='Sì' if fiber.is_dl_critical else 'No')
            ws.cell(row=idx, column=6, value='Sì' if fiber.is_ul_critical else 'No')
            if fiber.is_dl_critical or fiber.is_ul_critical:
                self._row_fill(ws, idx, BG_CRITICAL)

        self._autosize(ws)

    # ------------------------------------------------------------------ #
    #  8. SFP Modules                                                       #
    # ------------------------------------------------------------------ #

    def _sheet_sfp(self):
        ws = self.wb.create_sheet("SFP Modules")
        headers = ['Porta', 'FRU', 'Device Name', 'TX (dBm)', 'RX (dBm)',
                   'Temperatura', 'TN Backhaul', 'RX Critico (<-25dBm)']
        self._header_style(ws, headers, COLOR_GOLD)

        for idx, sfp in enumerate(self.analysis.sfp_modules.all(), start=2):
            ws.cell(row=idx, column=1, value=sfp.port)
            ws.cell(row=idx, column=2, value=sfp.fru)
            ws.cell(row=idx, column=3, value=sfp.device_name)
            ws.cell(row=idx, column=4, value=float(sfp.tx_dbm) if sfp.tx_dbm else '')
            ws.cell(row=idx, column=5, value=float(sfp.rx_dbm) if sfp.rx_dbm else '')
            ws.cell(row=idx, column=6, value=sfp.temperature if sfp.temperature else '')
            ws.cell(row=idx, column=7, value='Sì' if sfp.is_tn_backhaul else 'No')
            ws.cell(row=idx, column=8, value='Sì' if sfp.is_rx_critical else 'No')
            if sfp.is_rx_critical:
                self._row_fill(ws, idx, BG_CRITICAL)

        self._autosize(ws)

    # ------------------------------------------------------------------ #
    #  9. Branch Pairs                                                     #
    # ------------------------------------------------------------------ #

    def _sheet_branch_pairs(self):
        ws = self.wb.create_sheet("Branch Pairs")
        headers = ['FRU', 'Board', 'RF Port', 'Branch Pair', 'Risultato',
                   'Warning (OKW)', 'Critical (NOK)']
        self._header_style(ws, headers, COLOR_DARK)

        for idx, bp in enumerate(self.analysis.branch_pairs.all(), start=2):
            ws.cell(row=idx, column=1, value=bp.fru)
            ws.cell(row=idx, column=2, value=bp.board)
            ws.cell(row=idx, column=3, value=bp.rf_port)
            ws.cell(row=idx, column=4, value=bp.branch_pair)
            ws.cell(row=idx, column=5, value=bp.result)
            ws.cell(row=idx, column=6, value='Sì' if bp.is_warning else 'No')
            ws.cell(row=idx, column=7, value='Sì' if bp.is_critical else 'No')
            if bp.is_critical:
                self._row_fill(ws, idx, BG_CRITICAL)
            elif bp.is_warning:
                self._row_fill(ws, idx, BG_WARNING)

        self._autosize(ws)
