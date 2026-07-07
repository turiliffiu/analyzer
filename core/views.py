from django.contrib.auth.views import LoginView, LogoutView
"""
Views - Ericsson Universal Log Analyzer
"""
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, DetailView, ListView
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView

from .models import (
    LgaAlarm,
    AlarmPort,
    LogFile, Analysis, RadioUnit, Alarm, FRU, PuschData,
    RETDevice, TMADevice, FiberLink, SFPModule, BranchPair,
    TNBackhaul,
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
from parsers.tn_backhaul_parser import TNBackhaulParser
from parsers.lga_parser import LgaParser
from parsers.alarm_port_parser import AlarmPortParser


class UploadView(LoginRequiredMixin, TemplateView):
    """View per upload file log Ericsson"""
    template_name = 'core/upload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = LogFileUploadForm()
        return context

    def post(self, request):
        """Gestisce upload multi-file e avvia parsing aggregato"""
        files = request.FILES.getlist('files')

        if not files:
            return JsonResponse({'error': 'Nessun file selezionato'}, status=400)

        for f in files:
            if not f.name.endswith(('.txt', '.log')):
                return JsonResponse({'error': f'File {f.name}: solo .txt o .log accettati'}, status=400)
            if f.size > 50 * 1024 * 1024:
                return JsonResponse({'error': f'File {f.name} troppo grande (max 50MB)'}, status=400)

        try:
            analysis = self._parse_and_save(files, request.user)
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
    def _parse_and_save(self, files, user):
        """Parsa uno o più file log e aggrega i dati in una singola Analysis"""

        # --- Crea Analysis vuota ---
        analysis = Analysis.objects.create(user=user)

        apparati = []
        all_radio_data = []
        all_alarm_data = []
        all_fru_data = []
        all_pusch_data = []
        all_ret_tma_data = {'ret': [], 'tma': []}
        all_fiber_data = []
        all_sfp_data = []
        all_branch_data = []
        all_tn_data = []
        all_lga_data = []
        all_alarm_port_data = []

        for file_obj in files:
            # Leggi contenuto
            try:
                text = file_obj.read().decode('utf-8')
            except UnicodeDecodeError:
                file_obj.seek(0)
                text = file_obj.read().decode('latin-1')
            file_obj.seek(0)

            # Estrai metadati
            base_parser = BaseParser(text)
            metadata = base_parser.extract_metadata()
            apparato = metadata.get('apparato_nome', file_obj.name)
            apparati.append(apparato)

            # Salva LogFile collegato all'Analysis
            log_file = LogFile.objects.create(
                analysis=analysis,
                filename=file_obj.name,
                file=file_obj,
                file_size=file_obj.size,
                uploaded_by=user,
                apparato_nome=apparato,
                timestamp=metadata.get('timestamp', ''),
                ip_address=metadata.get('ip_address'),
                sw_version=metadata.get('sw_version', ''),
            )

            # --- Parsing con tag apparato ---
            radio_data = RadioParser(text).parse()
            for item in radio_data:
                item['apparato'] = apparato
            all_radio_data.extend(radio_data)

            alarm_data = AlarmParser(text).parse()
            for item in alarm_data:
                item['apparato'] = apparato
            all_alarm_data.extend(alarm_data)

            fru_data = FRUParser(text).parse()
            for item in fru_data:
                item['apparato'] = apparato
            all_fru_data.extend(fru_data)

            pusch_data = PuschParser(text).parse()
            for item in pusch_data:
                item['apparato'] = apparato
            all_pusch_data.extend(pusch_data)

            ret_tma = RETParser(text).parse()
            for item in ret_tma.get('ret', []):
                item['apparato'] = apparato
            for item in ret_tma.get('tma', []):
                item['apparato'] = apparato
            all_ret_tma_data['ret'].extend(ret_tma.get('ret', []))
            all_ret_tma_data['tma'].extend(ret_tma.get('tma', []))

            fiber_data = FiberParser(text).parse()
            for item in fiber_data:
                item['apparato'] = apparato
            all_fiber_data.extend(fiber_data)

            sfp_data = SFPParser(text).parse()
            for item in sfp_data:
                item['apparato'] = apparato
            all_sfp_data.extend(sfp_data)

            branch_data = BranchParser(text).parse()
            for item in branch_data:
                item['apparato'] = apparato
            all_branch_data.extend(branch_data)

            tn_data = TNBackhaulParser(text).parse()
            for item in tn_data:
                item['apparato'] = apparato
            all_tn_data.extend(tn_data)

            lga_data = LgaParser(text).parse()
            for item in lga_data:
                item['apparato'] = apparato
            all_lga_data.extend(lga_data)

            alarm_port_data = AlarmPortParser(text).parse()
            for item in alarm_port_data:
                item['apparato'] = apparato
            all_alarm_port_data.extend(alarm_port_data)

        # --- Nome aggregato Analysis ---
        analysis.apparato_nome = ' + '.join(apparati)
        analysis.save()

        # --- Salva tutti i record nel DB ---
        for item in all_radio_data:
            RadioUnit.objects.create(
                analysis=analysis,
                apparato=item.get('apparato', ''),
                fru=item['fru'], board=item['board'],
                rf_port=item['rf_port'], branch_pair=item['branch_pair'],
                tx=item.get('tx'), tx_unit=item.get('tx_unit') or '',
                vswr=item['vswr'] or 0, return_loss=item.get('return_loss'),
                rx=item.get('rx'),
                is_vswr_warning=item.get('is_vswr_warning') or False,
                is_vswr_critical=item.get('is_vswr_critical') or False,
                cell_id=item.get('cell_id', ''),
            )

        for item in all_alarm_data:
            Alarm.objects.create(
                analysis=analysis, apparato=item.get('apparato', ''),
                severity=item['severity'], alarm_number=item['alarm_number'],
                cause=item['cause'],
            )

        for item in all_fru_data:
            FRU.objects.create(
                analysis=analysis, apparato=item.get('apparato', ''),
                name=item['name'], board=item['board'],
                lnh=item.get('lnh', ''), status=item.get('status', ''),
                fault=item.get('fault', ''), oper=item.get('oper', ''),
                maint=item.get('maint', ''), stat=item.get('stat', ''),
                product_number=item.get('product_number', ''),
                rev=item.get('rev', ''), serial=item.get('serial', ''),
                date=item.get('date', ''), pmtemp=item.get('pmtemp', ''),
                temp=item.get('temp'), upt=item.get('upt', ''),
                volt=item.get('volt', ''), sw=item.get('sw', ''),
                is_temp_high=item.get('is_temp_high', False),
            )

        for item in all_pusch_data:
            PuschData.objects.create(
                analysis=analysis, apparato=item.get('apparato', ''),
                cell=item['cell'], sc=item['sc'],
                fru=item['fru'], board=item['board'],
                pusch=item['pusch'], pucch=item['pucch'],
                port_a=item.get('port_a'), port_b=item.get('port_b'),
                port_c=item.get('port_c'), port_d=item.get('port_d'),
                delta=item.get('delta'),
                is_rssi_high=item.get('is_rssi_high', False),
            )

        for item in all_ret_tma_data['ret']:
            RETDevice.objects.create(analysis=analysis, apparato=item.get('apparato', ''), **{k: v for k, v in item.items() if k != 'apparato'})
        for item in all_ret_tma_data['tma']:
            TMADevice.objects.create(analysis=analysis, apparato=item.get('apparato', ''), **{k: v for k, v in item.items() if k != 'apparato'})

        for item in all_fiber_data:
            FiberLink.objects.create(
                analysis=analysis, apparato=item.get('apparato', ''),
                link_id=item.get('link_id', ''), link_status=item.get('link_status', ''),
                ril=item.get('ril', ''), wl1=item.get('wl1'), temp1=item.get('temp1'),
                txbs1=item.get('txbs1'), txdbm1=item.get('txdbm1'), rxdbm1=item.get('rxdbm1'),
                wl2=item.get('wl2'), temp2=item.get('temp2'), txbs2=item.get('txbs2'),
                txdbm2=item.get('txdbm2'), rxdbm2=item.get('rxdbm2'),
                dl_loss=item.get('dl_loss'), ul_loss=item.get('ul_loss'),
                length=item.get('length'),
                is_dl_critical=item.get('is_dl_critical', False),
                is_ul_critical=item.get('is_ul_critical', False),
                is_link_down=item.get('is_link_down', False),
            )

        for item in all_sfp_data:
            SFPModule.objects.create(
                analysis=analysis, apparato=item.get('apparato', ''),
                port=item['port'], fru=item['fru'],
                device_name=item.get('device_name', ''),
                ril=item.get('ril', ''), board=item.get('board', ''),
                lnh=item.get('lnh', ''), vendor=item.get('vendor', ''),
                rev=item.get('rev', ''), serial=item.get('serial', ''),
                date=item.get('date', ''), ericsson_product=item.get('ericsson_product', ''),
                wl=item.get('wl'), temperature=item.get('temperature'),
                txbs=item.get('txbs'), tx_dbm=item.get('tx_dbm'),
                rx_dbm=item.get('rx_dbm'),
                is_tn_backhaul=item.get('is_tn_backhaul', False),
                is_rx_critical=item.get('is_rx_critical', False),
            )

        for item in all_branch_data:
            BranchPair.objects.create(
                analysis=analysis, apparato=item.get('apparato', ''),
                fru=item['fru'], board=item['board'],
                rf_port=item['rf_port'], branch_pair=item['branch_pair'],
                result=item['result'],
                is_warning=item.get('is_warning', False),
                is_critical=item.get('is_critical', False),
            )

        for item in all_tn_data:
            TNBackhaul.objects.create(
                analysis=analysis, apparato=item.get('apparato', ''),
                board=item['board'], lnh=item['lnh'], port=item['port'],
                vendor=item['vendor'], vendor_product=item['vendor_product'],
                revision=item['revision'], serial=item['serial'],
                date=item['date'], ericsson_product=item['ericsson_product'],
                wavelength=item.get('wavelength'), temperature=item.get('temperature'),
                tx_bias=item.get('tx_bias'), tx_dbm=item.get('tx_dbm'),
                rx_dbm=item.get('rx_dbm'),
                is_rx_critical=item.get('is_rx_critical', False),
                has_optical_data=item.get('has_optical_data', False),
            )

        for item in all_lga_data:
            LgaAlarm.objects.create(
                analysis=analysis, apparato=item.get('apparato', ''),
                timestamp=item['timestamp'], severity=item['severity'],
                specific_problem=item['specific_problem'],
                managed_object=item.get('managed_object', ''),
                additional_info=item.get('additional_info', ''),
            )

        for item in all_alarm_port_data:
            AlarmPort.objects.create(
                analysis=analysis, apparato=item.get('apparato', ''),
                fru=item['fru'], alarm_port=item['alarm_port'],
                active_external_alarm=item['active_external_alarm'],
                administrative_state_code=item['administrative_state_code'],
                administrative_state_label=item['administrative_state_label'],
                alarm_slogan=item['alarm_slogan'],
                normally_open=item['normally_open'],
            )

        # --- Aggiorna contatori ---
        analysis.radio_units_count = len(all_radio_data)
        analysis.alarms_critical_count = sum(1 for a in all_alarm_data if a['severity'] == 'CRITICAL')
        analysis.alarms_major_count = sum(1 for a in all_alarm_data if a['severity'] == 'MAJOR')
        analysis.alarms_minor_count = sum(1 for a in all_alarm_data if a['severity'] == 'MINOR')
        analysis.vswr_critical_count = sum(1 for r in all_radio_data if r.get('is_vswr_critical'))
        analysis.fru_count = len(all_fru_data)
        analysis.ret_count = len(all_ret_tma_data['ret'])
        analysis.tma_count = len(all_ret_tma_data['tma'])
        analysis.fiber_links_count = len(all_fiber_data)
        analysis.sfp_modules_count = len(all_sfp_data)
        analysis.pusch_cells_count = len(all_pusch_data)
        analysis.save()

        return analysis


class DashboardView(LoginRequiredMixin, ListView):
    """Dashboard principale con storico analisi e statistiche aggregate"""
    model = Analysis
    template_name = 'core/dashboard.html'
    context_object_name = 'analyses'
    paginate_by = 20
    ordering = ['-created_at']

    def get_queryset(self):
        """Filtra analisi in base al ruolo utente"""
        user = self.request.user
        
        # Admin vede tutto
        if user.is_superuser or (hasattr(user, 'profile') and user.profile.is_admin()):
            return Analysis.objects.all().order_by('-created_at')
        
        # Tecnico e Viewer vedono solo le proprie
        return Analysis.objects.filter(user=user).order_by('-created_at')

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

    def get_queryset(self):
        """Filtra analisi - admin vede tutto, altri solo proprie"""
        user = self.request.user
        if user.is_superuser or (hasattr(user, 'profile') and user.profile.is_admin()):
            return Analysis.objects.all()
        return Analysis.objects.filter(user=user)

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
        context['tn_backhaul'] = analysis.tn_backhaul.all()
        context['sfp_modules'] = analysis.sfp_modules.all()
        context['branch_pairs'] = analysis.branch_pairs.all()
        context['lga_alarms'] = analysis.lga_alarms.all()
        context['alarm_ports'] = analysis.alarm_ports.all()

        return context


class ExportExcelView(LoginRequiredMixin, DetailView):
    """Export analisi in formato Excel multi-sheet"""
    model = Analysis

    def get(self, request, *args, **kwargs):
        analysis = self.get_object()

        from exports.excel_exporter import ExcelExporter
        exporter = ExcelExporter(analysis)
        excel_file = exporter.generate()

        apparato = analysis.apparato_nome or 'ericsson'
        data_str = analysis.created_at.strftime('%Y%m%d')
        filename = f'ericsson_{apparato}_{data_str}.xlsx'

        response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# ============================================
# DELETE VIEWS


# ============================================
# AUTHENTICATION VIEWS
# ============================================

class CustomLoginView(LoginView):
    """Login view personalizzata"""
    template_name = 'core/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return '/dashboard/'


class CustomLogoutView(LogoutView):
    """Logout view personalizzata"""
    next_page = '/login/'
# ============================================


class DeleteAnalysisView(View):
    """Elimina una singola analisi"""
    
    def post(self, request, pk):
        try:
            analysis = Analysis.objects.get(pk=pk)
            
            # Verifica ownership (admin può eliminare tutto, altri solo proprie)
            user = request.user
            if not user.is_superuser:
                if hasattr(user, 'profile') and user.profile.is_admin():
                    pass  # Admin può eliminare tutto
                elif analysis.user != user:
                    messages.error(request, '❌ Non hai i permessi per eliminare questa analisi')
                    return redirect('core:dashboard')
            
            apparato = analysis.apparato_nome
            analysis.delete()
            messages.success(request, f'✅ Analisi apparato {apparato} eliminata con successo')
        except Analysis.DoesNotExist:
            messages.error(request, '❌ Analisi non trovata')
        except Exception as e:
            messages.error(request, f'❌ Errore durante eliminazione: {str(e)}')
        
        return redirect('core:dashboard')


class DeleteAllAnalysesView(View):
    """Elimina tutte le analisi"""
    
    def post(self, request):
        try:
            user = request.user
            
            # Admin può eliminare tutto, altri solo le proprie
            if user.is_superuser or (hasattr(user, 'profile') and user.profile.is_admin()):
                analyses = Analysis.objects.all()
            else:
                analyses = Analysis.objects.filter(user=user)
            
            count = analyses.count()
            if count > 0:
                analyses.delete()
                messages.success(request, f'✅ {count} analisi eliminate con successo')
            else:
                messages.info(request, 'ℹ️ Nessuna analisi da eliminare')
        except Exception as e:
            messages.error(request, f'❌ Errore durante eliminazione: {str(e)}')
        
        return redirect('core:dashboard')


class LgaTrendView(LoginRequiredMixin, DetailView):
    """Dashboard trend analysis degli allarmi LGA"""
    model = Analysis
    template_name = 'core/lga_trend.html'
    context_object_name = 'analysis'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or (hasattr(user, 'profile') and user.profile.is_admin()):
            return Analysis.objects.all()
        return Analysis.objects.filter(user=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analysis = self.object
        qs = analysis.lga_alarms.all()

        # --- Filtro periodo da querystring ---
        date_from     = self.request.GET.get('date_from', '')
        date_to       = self.request.GET.get('date_to', '')
        preset        = self.request.GET.get('preset', '')
        filter_sev    = self.request.GET.get('severity', '')

        from django.utils import timezone as tz
        from datetime import timedelta

        if preset == '24h':
            qs = qs.filter(timestamp__gte=tz.now() - timedelta(hours=24))
        elif preset == '7d':
            qs = qs.filter(timestamp__gte=tz.now() - timedelta(days=7))
        elif preset == '30d':
            qs = qs.filter(timestamp__gte=tz.now() - timedelta(days=30))
        else:
            if date_from:
                try:
                    from datetime import datetime
                    df = datetime.strptime(date_from, '%Y-%m-%d')
                    qs = qs.filter(timestamp__date__gte=df.date())
                except ValueError:
                    pass
            if date_to:
                try:
                    from datetime import datetime
                    dt = datetime.strptime(date_to, '%Y-%m-%d')
                    qs = qs.filter(timestamp__date__lte=dt.date())
                except ValueError:
                    pass

        # --- Filtro severità (applicato DOPO il filtro periodo) ---
        if filter_sev == 'raised':
            qs_filtered = qs.exclude(severity='*')
        elif filter_sev:
            qs_filtered = qs.filter(severity=filter_sev)
        else:
            qs_filtered = qs

        # --- Cards sinottiche ---
        from django.db.models import Count
        total   = qs.count()
        raised  = qs.exclude(severity='*').count()
        ceased  = qs.filter(severity='*').count()
        by_sev  = {s: 0 for s in ['C', 'M', 'm', 'w', '*']}
        for row in qs.values('severity').annotate(n=Count('id')):
            by_sev[row['severity']] = row['n']

        # Usa qs_filtered per tabella e timeline
        qs = qs_filtered

        # --- Tabella per tipo allarme ---
        from collections import defaultdict
        alarm_groups = defaultdict(lambda: {
            'raised': 0, 'ceased': 0, 'first': None, 'last': None, 'managed_objects': set()
        })
        for alarm in qs.order_by('timestamp'):
            sp = alarm.specific_problem or '(sconosciuto)'
            g  = alarm_groups[sp]
            if alarm.severity == '*':
                g['ceased'] += 1
            else:
                g['raised'] += 1
            if g['first'] is None:
                g['first'] = alarm.timestamp
            g['last'] = alarm.timestamp
            if alarm.managed_object:
                g['managed_objects'].add(alarm.managed_object)

        alarm_summary = []
        for sp, g in sorted(alarm_groups.items(), key=lambda x: -x[1]['raised']):
            net = g['raised'] - g['ceased']
            alarm_summary.append({
                'specific_problem': sp,
                'raised':  g['raised'],
                'ceased':  g['ceased'],
                'net':     net,
                'status':  'ATTIVO' if net > 0 else 'RISOLTO',
                'first':   g['first'],
                'last':    g['last'],
                'managed_objects': ', '.join(sorted(g['managed_objects']))[:120],
            })

        # --- Dati timeline per Chart.js (raggruppati per ora) ---
        from collections import OrderedDict
        timeline = OrderedDict()
        for alarm in qs.order_by('timestamp'):
            hour_key = alarm.timestamp.strftime('%Y-%m-%d %H:00')
            if hour_key not in timeline:
                timeline[hour_key] = {'C': 0, 'M': 0, 'm': 0, 'w': 0, '*': 0}
            timeline[hour_key][alarm.severity] = timeline[hour_key].get(alarm.severity, 0) + 1

        import json
        context.update({
            'date_from':     date_from,
            'date_to':       date_to,
            'preset':        preset,
            'total':         total,
            'raised':        raised,
            'ceased':        ceased,
            'by_sev':        by_sev,
            'alarm_summary': alarm_summary,
            'timeline_labels': json.dumps(list(timeline.keys())),
            'timeline_critical': json.dumps([v['C'] for v in timeline.values()]),
            'timeline_major':    json.dumps([v['M'] for v in timeline.values()]),
            'timeline_minor':    json.dumps([v['m'] for v in timeline.values()]),
            'timeline_warning':  json.dumps([v['w'] for v in timeline.values()]),
            'timeline_ceasing':  json.dumps([v['*'] for v in timeline.values()]),
            'filter_sev':        filter_sev,
        })
        return context


class ExportPreSwapView(LoginRequiredMixin, DetailView):
    """Export Pre Swap: Radio VSWR, Allarmi, RET, Alarm Ports"""
    model = Analysis

    def get(self, request, *args, **kwargs):
        analysis = self.get_object()

        from exports.excel_exporter import ExcelExporter
        exporter = ExcelExporter(analysis)
        excel_file = exporter.generate_preswap()

        apparato = analysis.apparato_nome or 'ericsson'
        data_str = analysis.created_at.strftime('%Y%m%d')
        filename = f'preswap_{apparato}_{data_str}.xlsx'

        response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


import json
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt


class SintesiView(LoginRequiredMixin, TemplateView):
    """Pagina Sintesi Multi-Excel con gestione pattern esclusione"""
    template_name = 'core/sintesi_excel.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import AlarmExcludePattern
        patterns = list(AlarmExcludePattern.objects.values('id', 'pattern'))
        context['patterns_json'] = json.dumps(patterns)
        return context


@login_required
def alarm_pattern_add(request):
    """Aggiunge un pattern di esclusione"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    from .models import AlarmExcludePattern
    try:
        data = json.loads(request.body)
        pattern = data.get('pattern', '').strip()
        if not pattern:
            return JsonResponse({'error': 'Pattern vuoto'}, status=400)
        obj, created = AlarmExcludePattern.objects.get_or_create(
            pattern=pattern,
            defaults={'created_by': request.user}
        )
        return JsonResponse({'id': obj.id, 'pattern': obj.pattern, 'created': created})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def alarm_pattern_delete(request, pk):
    """Rimuove un pattern di esclusione"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    from .models import AlarmExcludePattern
    try:
        AlarmExcludePattern.objects.filter(pk=pk).delete()
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
