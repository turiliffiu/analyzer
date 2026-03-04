"""
Views - Ericsson Universal Log Analyzer
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, DetailView, ListView
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.contrib import messages

from .models import (
    LogFile, Analysis, RadioUnit, Alarm, FRU, PuschData,
    RETDevice, TMADevice, FiberLink, SFPModule, BranchPair
)
from .forms import LogFileUploadForm

# Import parser con path relativo alla root del progetto
from parsers.base_parser import BaseParser
from parsers.radio_parser import RadioParser
from parsers.pusch_parser import PuschParser
from parsers.alarm_parser import AlarmParser
from parsers.fru_parser import FRUParser
from parsers.ret_parser import RETParser
from parsers.fiber_parser import FiberParser
from parsers.sfp_parser import SFPParser
from parsers.branch_parser import BranchParser


class UploadView(LoginRequiredMixin, TemplateView):
    """View per upload file log Ericsson"""
    template_name = 'core/upload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = LogFileUploadForm()
        return context

    def post(self, request):
        """Gestisce upload file e avvia parsing automatico"""
        form = LogFileUploadForm(request.POST, request.FILES)

        if not form.is_valid():
            errors = '; '.join([str(e) for errs in form.errors.values() for e in errs])
            return JsonResponse({'error': errors}, status=400)

        log_file_obj = request.FILES['file']

        try:
            # Leggi contenuto (UTF-8 con fallback latin-1)
            try:
                content = log_file_obj.read().decode('utf-8')
            except UnicodeDecodeError:
                log_file_obj.seek(0)
                content = log_file_obj.read().decode('latin-1')

            log_file_obj.seek(0)

            # Crea record LogFile
            log_file = LogFile.objects.create(
                uploaded_by=request.user,
                filename=log_file_obj.name,
                file=log_file_obj,
                file_size=log_file_obj.size
            )

            # Parse e salva tutto in database (transazione atomica)
            analysis = self._parse_and_save(log_file, content)

            return JsonResponse({
                'status': 'success',
                'analysis_id': analysis.id,
                'redirect_url': f'/analysis/{analysis.id}/'
            })

        except Exception as e:
            import traceback
            return JsonResponse({
                'error': str(e),
                'detail': traceback.format_exc()
            }, status=500)

    @transaction.atomic
    def _parse_and_save(self, log_file, content):
        """Parsa log ed esegue tutti i parser salvando su DB"""

        # Estrai metadati apparato
        base_parser = BaseParser(content)
        metadata = base_parser.extract_metadata()

        log_file.apparato_nome = metadata.get('apparato_nome', '')
        log_file.timestamp = metadata.get('timestamp', '')
        log_file.ip_address = metadata.get('ip_address')
        log_file.sw_version = metadata.get('sw_version', '')
        log_file.save()

        # Crea oggetto Analysis
        analysis = Analysis.objects.create(log_file=log_file)

        # --- 1. Radio Units (VSWR) ---
        radio_parser = RadioParser(content)
        radio_data = radio_parser.parse()
        for item in radio_data:
            RadioUnit.objects.create(
                analysis=analysis,
                fru=item['fru'],
                board=item['board'],
                rf_port=item['rf_port'],
                branch_pair=item['branch_pair'],
                tx=item.get('tx'),
                tx_unit=item.get('tx_unit') or '',
                vswr=item['vswr'] or 0,
                return_loss=item.get('return_loss'),
                rx=item.get('rx'),
                is_vswr_warning=item.get('is_vswr_warning') or False,
                is_vswr_critical=item.get('is_vswr_critical') or False,
            )

        # --- 2. Allarmi ---
        alarm_parser = AlarmParser(content)
        alarm_data = alarm_parser.parse()
        for item in alarm_data:
            Alarm.objects.create(
                analysis=analysis,
                severity=item['severity'],
                alarm_number=item['alarm_number'],
                cause=item['cause'],
            )

        # --- 3. FRU ---
        fru_parser = FRUParser(content)
        fru_data = fru_parser.parse()
        for item in fru_data:
            FRU.objects.create(
                analysis=analysis,
                name=item['name'],
                board=item['board'],
                pmtemp=item.get('pmtemp', ''),
                temp=item.get('temp'),
                is_temp_high=item.get('is_temp_high', False),
            )

        # --- 4. PUSCH/PUCCH ---
        pusch_parser = PuschParser(content)
        pusch_data = pusch_parser.parse()
        for item in pusch_data:
            PuschData.objects.create(
                analysis=analysis,
                cell=item['cell'],
                sc=item['sc'],
                fru=item['fru'],
                board=item['board'],
                pusch=item['pusch'],
                pucch=item['pucch'],
                port_a=item.get('port_a'),
                port_b=item.get('port_b'),
                port_c=item.get('port_c'),
                port_d=item.get('port_d'),
                delta=item.get('delta'),
                is_rssi_high=item.get('is_rssi_high', False),
            )

        # --- 5. RET / TMA ---
        ret_parser = RETParser(content)
        ret_tma_data = ret_parser.parse()
        for item in ret_tma_data.get('ret', []):
            RETDevice.objects.create(analysis=analysis, **item)
        for item in ret_tma_data.get('tma', []):
            TMADevice.objects.create(analysis=analysis, **item)

        # --- 6. Fiber Links ---
        fiber_parser = FiberParser(content)
        fiber_data = fiber_parser.parse()
        for item in fiber_data:
            FiberLink.objects.create(
                analysis=analysis,
                link=item['link'],
                fru=item['fru'],
                dl_loss=item.get('dl_loss'),
                ul_loss=item.get('ul_loss'),
                is_dl_critical=item.get('is_dl_critical', False),
                is_ul_critical=item.get('is_ul_critical', False),
            )

        # --- 7. SFP Modules ---
        sfp_parser = SFPParser(content)
        sfp_data = sfp_parser.parse()
        for item in sfp_data:
            SFPModule.objects.create(
                analysis=analysis,
                port=item['port'],
                fru=item['fru'],
                device_name=item.get('device_name', item.get('fru', '')),
                tx_dbm=item.get('tx_dbm'),
                rx_dbm=item.get('rx_dbm'),
                is_tn_backhaul=item.get('is_tn_backhaul', False),
                is_rx_critical=item.get('is_rx_critical', False),
            )

        # --- 8. Branch Pairs ---
        branch_parser = BranchParser(content)
        branch_data = branch_parser.parse()
        for item in branch_data:
            BranchPair.objects.create(
                analysis=analysis,
                fru=item['fru'],
                board=item['board'],
                rf_port=item['rf_port'],
                branch_pair=item['branch_pair'],
                result=item['result'],
                is_warning=item.get('is_warning', False),
                is_critical=item.get('is_critical', False),
            )

        # --- Aggiorna contatori statistici sull'Analysis ---
        analysis.radio_units_count = len(radio_data)
        analysis.alarms_critical_count = sum(1 for a in alarm_data if a['severity'] == 'CRITICAL')
        analysis.alarms_major_count = sum(1 for a in alarm_data if a['severity'] == 'MAJOR')
        analysis.alarms_minor_count = sum(1 for a in alarm_data if a['severity'] == 'MINOR')
        analysis.vswr_critical_count = sum(1 for r in radio_data if r.get('is_vswr_critical'))
        analysis.fru_count = len(fru_data)
        analysis.ret_count = len(ret_tma_data.get('ret', []))
        analysis.tma_count = len(ret_tma_data.get('tma', []))
        analysis.fiber_links_count = len(fiber_data)
        analysis.sfp_modules_count = len(sfp_data)
        analysis.pusch_cells_count = len(pusch_data)
        analysis.save()

        return analysis


class DashboardView(LoginRequiredMixin, ListView):
    """Dashboard principale con storico analisi e statistiche aggregate"""
    model = Analysis
    template_name = 'core/dashboard.html'
    context_object_name = 'analyses'
    paginate_by = 20
    ordering = ['-created_at']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Statistiche globali aggregate
        all_analyses = Analysis.objects.all()
        context['stats'] = {
            'total_analyses': all_analyses.count(),
            'total_critical': sum(a.alarms_critical_count for a in all_analyses),
            'total_vswr_critical': sum(a.vswr_critical_count for a in all_analyses),
            'total_radio_units': sum(a.radio_units_count for a in all_analyses),
        }
        return context


class AnalysisDetailView(LoginRequiredMixin, DetailView):
    """Dettaglio analisi con 9 tabelle dati"""
    model = Analysis
    template_name = 'core/analysis_detail.html'
    context_object_name = 'analysis'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analysis = self.object

        context['radio_units'] = analysis.radio_units.all()
        context['alarms_critical'] = analysis.alarms.filter(severity='CRITICAL')
        context['alarms_major'] = analysis.alarms.filter(severity='MAJOR')
        context['alarms_minor'] = analysis.alarms.filter(severity='MINOR')
        context['alarms'] = analysis.alarms.all()
        context['fru_units'] = analysis.fru_units.all()
        context['pusch_data'] = analysis.pusch_data.all()
        context['ret_devices'] = analysis.ret_devices.all()
        context['tma_devices'] = analysis.tma_devices.all()
        context['fiber_links'] = analysis.fiber_links.all()
        context['sfp_modules'] = analysis.sfp_modules.all()
        context['branch_pairs'] = analysis.branch_pairs.all()

        return context


class ExportExcelView(LoginRequiredMixin, DetailView):
    """Export analisi in formato Excel multi-sheet"""
    model = Analysis

    def get(self, request, *args, **kwargs):
        analysis = self.get_object()

        from exports.excel_exporter import ExcelExporter
        exporter = ExcelExporter(analysis)
        excel_file = exporter.generate()

        apparato = analysis.log_file.apparato_nome or 'ericsson'
        data_str = analysis.created_at.strftime('%Y%m%d')
        filename = f'ericsson_{apparato}_{data_str}.xlsx'

        response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
