"""
Models per Ericsson Universal Log Analyzer
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class LogFile(models.Model):
    """File di log caricato dall'utente"""
    
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='log_files')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='logs/%Y/%m/%d/')
    file_size = models.IntegerField(help_text="Dimensione file in bytes")
    
    # Metadati estratti dal log
    apparato_nome = models.CharField(max_length=100, blank=True)
    timestamp = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    sw_version = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "File Log"
        verbose_name_plural = "File Log"
    
    def __str__(self):
        return f"{self.apparato_nome or self.filename} - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"


class Analysis(models.Model):
    """Analisi completa di un log file"""
    
    log_file = models.OneToOneField(LogFile, on_delete=models.CASCADE, related_name='analysis')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analyses', null=True)  # null=True temporaneo per migration
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Statistiche globali
    radio_units_count = models.IntegerField(default=0)
    alarms_critical_count = models.IntegerField(default=0)
    alarms_major_count = models.IntegerField(default=0)
    alarms_minor_count = models.IntegerField(default=0)
    vswr_critical_count = models.IntegerField(default=0)
    fru_count = models.IntegerField(default=0)
    ret_count = models.IntegerField(default=0)
    tma_count = models.IntegerField(default=0)
    fiber_links_count = models.IntegerField(default=0)
    sfp_modules_count = models.IntegerField(default=0)
    pusch_cells_count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Analisi"
        verbose_name_plural = "Analisi"
    
    def __str__(self):
        return f"Analisi {self.log_file.apparato_nome} - {self.created_at.strftime('%Y-%m-%d')}"


class RadioUnit(models.Model):
    """Radio Unit con dati VSWR"""
    
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='radio_units')
    
    fru = models.CharField(max_length=50)  # Radio-S100-1
    board = models.CharField(max_length=50)  # RRU449944B144B3C
    rf_port = models.CharField(max_length=5)  # A, B, C, D
    branch_pair = models.CharField(max_length=10)  # 1A, 1B, etc.
    
    # Valori
    tx = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    tx_unit = models.CharField(max_length=10, blank=True)  # W, dBm
    vswr = models.DecimalField(max_digits=6, decimal_places=2)
    return_loss = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    rx = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Flags
    is_vswr_warning = models.BooleanField(default=False)  # > 1.25
    is_vswr_critical = models.BooleanField(default=False)  # > 1.50
    
    class Meta:
        ordering = ['fru', 'rf_port']
        verbose_name = "Radio Unit"
        verbose_name_plural = "Radio Units"
    
    def __str__(self):
        return f"{self.fru} Port {self.rf_port} - VSWR: {self.vswr}"


class Alarm(models.Model):
    """Allarme attivo"""
    
    SEVERITY_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('MAJOR', 'Major'),
        ('MINOR', 'Minor'),
    ]
    
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='alarms')
    
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    alarm_number = models.CharField(max_length=50)
    cause = models.TextField()
    
    class Meta:
        ordering = ['severity', 'alarm_number']
        verbose_name = "Allarme"
        verbose_name_plural = "Allarmi"
    
    def __str__(self):
        return f"{self.severity} - {self.alarm_number}"


class FRU(models.Model):
    """Field Replaceable Unit"""
    
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='fru_units')
    
    name = models.CharField(max_length=50)  # BB-1, Radio-S100-1
    board = models.CharField(max_length=100)
    lnh = models.CharField(max_length=20, blank=True)  # 000100, BXP_5
    status = models.CharField(max_length=10, blank=True)  # 1
    fault = models.CharField(max_length=10, blank=True)  # OFF/ON
    oper = models.CharField(max_length=10, blank=True)  # ON/OFF
    maint = models.CharField(max_length=10, blank=True)  # OFF/ON
    stat = models.CharField(max_length=10, blank=True)  # ON/N/A
    product_number = models.CharField(max_length=50, blank=True)  # KDU1370015/11
    rev = models.CharField(max_length=20, blank=True)  # R3D, R2D
    serial = models.CharField(max_length=50, blank=True)  # TD3X346968
    date = models.CharField(max_length=20, blank=True)  # 20211017
    pmtemp = models.CharField(max_length=20, blank=True)
    temp = models.IntegerField(null=True, blank=True)  # None per BB-1
    upt = models.CharField(max_length=50, blank=True)
    volt = models.CharField(max_length=20, blank=True)
    sw = models.CharField(max_length=100, blank=True)
    
    # Flags
    is_temp_high = models.BooleanField(default=False)  # > 60°C
    
    class Meta:
        ordering = ['name']
        verbose_name = "FRU"
        verbose_name_plural = "FRU"
    
    def __str__(self):
        return f"{self.name} - {self.board}"


class PuschData(models.Model):
    """Dati PUSCH/PUCCH RSSI"""
    
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='pusch_data')
    
    cell = models.CharField(max_length=50)  # FDD=MH45M2
    sc = models.CharField(max_length=50)
    fru = models.CharField(max_length=50)
    board = models.CharField(max_length=100)
    
    # Valori RSSI
    pusch = models.DecimalField(max_digits=6, decimal_places=1)
    pucch = models.DecimalField(max_digits=6, decimal_places=1)
    port_a = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    port_b = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    port_c = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    port_d = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    delta = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    # Flag critico
    is_rssi_high = models.BooleanField(default=False)  # > -110 dBm
    
    class Meta:
        ordering = ['cell']
        verbose_name = "PUSCH/PUCCH"
        verbose_name_plural = "PUSCH/PUCCH"
    
    def __str__(self):
        return f"{self.cell} - PUSCH: {self.pusch}"


class RETDevice(models.Model):
    """Dispositivo RET (Remote Electrical Tilt)"""
    
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='ret_devices')
    
    antenna_group = models.CharField(max_length=50)
    antenna_near_unit = models.CharField(max_length=50)
    radio_unit = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    device_type = models.CharField(max_length=50)
    product_nr = models.CharField(max_length=50, blank=True)
    revision = models.CharField(max_length=20, blank=True)
    unique_id = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['antenna_group', 'antenna_near_unit']
        verbose_name = "RET"
        verbose_name_plural = "RET"
    
    def __str__(self):
        return f"RET {self.antenna_group}/{self.antenna_near_unit}"


class TMADevice(models.Model):
    """Dispositivo TMA (Tower Mounted Amplifier)"""
    
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='tma_devices')
    
    antenna_group = models.CharField(max_length=50)
    antenna_near_unit = models.CharField(max_length=50)
    radio_unit = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    device_type = models.CharField(max_length=50)
    product_nr = models.CharField(max_length=50, blank=True)
    revision = models.CharField(max_length=20, blank=True)
    unique_id = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['antenna_group', 'antenna_near_unit']
        verbose_name = "TMA"
        verbose_name_plural = "TMA"
    
    def __str__(self):
        return f"TMA {self.antenna_group}/{self.antenna_near_unit}"


class FiberLink(models.Model):
    """Collegamento Fibra Ottica - dati completi entrambi i lati"""
    
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='fiber_links')
    
    # Identificazione
    link_id = models.CharField(max_length=10)  # 1, 2, 3
    link_status = models.CharField(max_length=10)  # Up, Down
    ril = models.CharField(max_length=50)  # S210-1, S110-1
    
    # Lato 1 (Master/BB)
    wl1 = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)  # 1310.00
    temp1 = models.IntegerField(null=True, blank=True)  # 46 (estratto da "46C")
    txbs1 = models.IntegerField(null=True, blank=True)  # 42 (estratto da "42%")
    txdbm1 = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)  # -2.77
    rxdbm1 = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)  # -1.94
    
    # Lato 2 (Slave/RRU)
    wl2 = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)  # 1310.00
    temp2 = models.IntegerField(null=True, blank=True)  # 38
    txbs2 = models.IntegerField(null=True, blank=True)  # 40
    txdbm2 = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)  # -3.36
    rxdbm2 = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)  # -2.68
    
    # Loss e dati link
    dl_loss = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)  # -0.09
    ul_loss = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)  # -1.42
    length = models.CharField(max_length=20, blank=True)  # 52m, 100m
    
    # Flags
    is_dl_critical = models.BooleanField(default=False)  # |DlLoss| > 3.5
    is_ul_critical = models.BooleanField(default=False)  # |UlLoss| > 3.5
    is_link_down = models.BooleanField(default=False)  # link_status != Up
    
    class Meta:
        ordering = ['link_id']
        verbose_name = "Fiber Link"
        verbose_name_plural = "Fiber Links"
    
    def __str__(self):
        return f"Link {self.link_id} - {self.ril}"
class SFPModule(models.Model):
    """Modulo SFP"""
    
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='sfp_modules')
    
    port = models.CharField(max_length=50)
    fru = models.CharField(max_length=50)
    device_name = models.CharField(max_length=100)
    
    # Identificazione completa
    ril = models.CharField(max_length=50, blank=True)  # S210-1
    board = models.CharField(max_length=100, blank=True)  # BB6648
    lnh = models.CharField(max_length=20, blank=True)  # 000100
    vendor = models.CharField(max_length=100, blank=True)  # ERICSSON
    rev = models.CharField(max_length=20, blank=True)  # 1.0
    serial = models.CharField(max_length=50, blank=True)  # PM85275441
    date = models.CharField(max_length=20, blank=True)  # 20211020
    ericsson_product = models.CharField(max_length=100, blank=True)  # RDH10265/2 R1A
    wl = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)  # 1310.00
    txbs = models.IntegerField(null=True, blank=True)  # 42 (estratto da 42%)
    
    # Valori
    tx_dbm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    rx_dbm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    temperature = models.IntegerField(null=True, blank=True)
    
    # Link type
    is_tn_backhaul = models.BooleanField(default=False)
    
    # Flags
    is_rx_critical = models.BooleanField(default=False)  # < -25 dBm
    
    class Meta:
        ordering = ['port']
        verbose_name = "Modulo SFP"
        verbose_name_plural = "Moduli SFP"
    
    def __str__(self):
        return f"{self.port} - {self.device_name}"


class BranchPair(models.Model):
    """Branch Pair Analysis"""
    
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='branch_pairs')
    
    fru = models.CharField(max_length=50)
    board = models.CharField(max_length=100)
    rf_port = models.CharField(max_length=5)
    branch_pair = models.CharField(max_length=10)
    
    # Test results
    result = models.CharField(max_length=10)  # OK, OKW, NOK
    
    # Flags
    is_warning = models.BooleanField(default=False)
    is_critical = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['fru', 'rf_port']
        verbose_name = "Branch Pair"
        verbose_name_plural = "Branch Pairs"
    
    def __str__(self):
        return f"{self.fru} {self.rf_port} - {self.result}"


class UserProfile(models.Model):
    """Profilo esteso utente con ruoli"""
    
    ROLE_CHOICES = [
        ('admin', 'Amministratore'),
        ('tecnico', 'Tecnico'),
        ('viewer', 'Visualizzatore'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='tecnico')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Profilo Utente"
        verbose_name_plural = "Profili Utenti"
    
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
    
    def is_admin(self):
        return self.role == 'admin' or self.user.is_superuser
    
    def is_tecnico(self):
        return self.role == 'tecnico'
    
    def is_viewer(self):
        return self.role == 'viewer'
    
    def can_edit(self):
        """Può creare/modificare analisi"""
        return self.role in ['admin', 'tecnico']
    
    def can_delete(self):
        """Può eliminare analisi"""
        return self.role == 'admin' or self.role == 'tecnico'


class TNBackhaul(models.Model):
    """Transport Network Backhaul - porte TN"""
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name='tn_backhaul')
    
    # Identificazione
    board = models.CharField(max_length=50)  # BB6648
    lnh = models.CharField(max_length=20)    # 000100
    port = models.CharField(max_length=10)   # IB, IA2
    
    # Vendor info
    vendor = models.CharField(max_length=50)
    vendor_product = models.CharField(max_length=100)
    revision = models.CharField(max_length=20)
    serial = models.CharField(max_length=50)
    date = models.CharField(max_length=20)
    ericsson_product = models.CharField(max_length=100)
    
    # Dati ottici (possono essere NA)
    wavelength = models.CharField(max_length=20, null=True, blank=True)
    temperature = models.IntegerField(null=True, blank=True)  # °C
    tx_bias = models.CharField(max_length=10, null=True, blank=True)  # %
    tx_dbm = models.FloatField(null=True, blank=True)
    rx_dbm = models.FloatField(null=True, blank=True)
    
    # Flags
    is_rx_critical = models.BooleanField(default=False)
    has_optical_data = models.BooleanField(default=False)  # False se tutti NA
    
    class Meta:
        ordering = ['port']
        verbose_name = "TN Backhaul"
        verbose_name_plural = "TN Backhaul Ports"
    
    def __str__(self):
        return f"{self.board} {self.port} - {self.vendor}"


class LgaAlarm(models.Model):
    """Allarme da comando LGA (Alarm Log Ericsson)"""

    SEVERITY_CHOICES = [
        ('C', 'Critical'),
        ('M', 'Major'),
        ('m', 'minor'),
        ('w', 'Warning'),
        ('*', 'Ceasing'),
    ]

    analysis = models.ForeignKey(
        Analysis, on_delete=models.CASCADE, related_name='lga_alarms'
    )
    timestamp = models.DateTimeField()
    severity = models.CharField(max_length=1, choices=SEVERITY_CHOICES)
    specific_problem = models.CharField(max_length=500)
    managed_object = models.CharField(max_length=500, blank=True)
    additional_info = models.TextField(blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = "LGA Alarm"
        verbose_name_plural = "LGA Alarms"

    def __str__(self):
        return f"{self.timestamp} [{self.get_severity_display()}] {self.specific_problem}"

    @property
    def severity_label(self):
        """Etichetta leggibile della severità"""
        return dict(self.SEVERITY_CHOICES).get(self.severity, self.severity)

    @property
    def is_active(self):
        """True se l'allarme è attivo (non ceasing)"""
        return self.severity != '*'
