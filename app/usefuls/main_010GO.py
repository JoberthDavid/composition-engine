# Para consultar sobre a biblioteca xlsxwriter https://xlsxwriter.readthedocs.io/index.html 
# Para consultar sobre a biblioteca Pandas https://www.dataquest.io/blog/excel-and-pandas/
# https://medium.com/analytics-vidhya/common-excel-formulas-in-python-c5a7ce0ae07a

import math

from arquivos import (
                        arq_db_cp,
                        arq_db_in,
                        arq_apr_in,
                        arq_cto_in,
                        arq_db_al_an,
                        arq_db_al_st,
                        arq_apr_al,
                        arq_dmt,
                    )

from funcoes import escrever_arquivo_excel
from projeto import BaseDF, Servico, BonificacaoDespesasIndiretas, Projeto, GeradorDF

from formatacao_dados import Data, DadosProjeto, Precisao


baseDF = BaseDF( arq_db_cp, arq_db_in, arq_apr_in, arq_cto_in )

prazo_execucao_ano = 2


con_rot = "01 - Conservação corretiva rotineira"
ser_aux_rot = '02 - Auxiliares - conserva corretiva rotineira'

con_rot_men = '03 - Conservação corretiva rotineira - mensal'

con_pre_per = '04 - Conservação preventiva periódica'

ser_aux_pre = '07 - Auxiliares - DSM e conservação preventiva periódica'

con_emerg = '05 - Conservação de emergência'

dsm = '06 - Demais serviços de engenharia'
sin_obra = '08 - Sinalização de obras'


ser_aux_transp_pv = '09- Auxiliares - transportes em rodovias pavimentadas'
ser_aux_transp_rp = '10 - Auxiliares - transportes em rodovias revestimento primário'

adm_loc = '11 - Administração local'
mob_des = '12 - Mobilização e desmobilização'
can_ins = '13 - Instalações provisórias e industriais'


lista_servico_proj1 = [

Servico( con_rot, '1107892', Precisao().quantidade(18.649*2), False, False, False ),
Servico( con_rot, '1600436', Precisao().quantidade(0.184*2), False, False, False ),
Servico( con_rot, '1600896', Precisao().quantidade(1704.75*2), False, False, False ),
Servico( con_rot, '1600898', Precisao().quantidade(909.2*2), False, False, False ),
Servico( con_rot, '3103302', Precisao().quantidade(74.820*2), False, False, False ),
Servico( con_rot, '3108022', Precisao().quantidade(14.964*2), False, False, False ),
Servico( con_rot, '3815706', Precisao().quantidade(67.838*2), False, False, True ),
Servico( con_rot, '4915623', Precisao().quantidade(122.742*2), False, False, False ),
Servico( con_rot, '4915631', Precisao().quantidade(153.428*2), False, False, True ),
Servico( con_rot, '4915730', Precisao().quantidade(2944.000*2), False, False, False ),
Servico( con_rot, '4915733', Precisao().quantidade(248.632*2), False, False, False ),
Servico( con_rot, '4915734', Precisao().quantidade(1491.792*2), False, False, False ),
Servico( con_rot, '4915757', Precisao().quantidade(340.950*2), False, False, True ),
Servico( con_rot, '4915764', Precisao().quantidade(545.520*2), False, False, True ),
Servico( con_rot, '4915766', Precisao().quantidade(545.520*2), False, False, True ),
Servico( con_rot, '4915774', Precisao().quantidade(49.726*2), False, False, False ),
Servico( con_rot, '8888306', Precisao().quantidade(340.950*2), True, False, False ),
Servico( con_rot, '8888322', Precisao().quantidade(153.428*2), True, False, False ),
Servico( con_rot, '8888344', Precisao().quantidade(891.925*2), True, False, False ),
Servico( con_rot, '8888350', Precisao().quantidade(891.925*2), True, False, False ),
Servico( con_rot, '8888356', Precisao().quantidade(891.925*2), True, False, False ),
Servico( con_rot, '8888378', Precisao().quantidade(153.428*2), True, False, False ),
Servico( con_rot, '8888394', Precisao().quantidade(340.950*2), True, False, False ),

Servico( con_rot_men, '9999100', Precisao().quantidade(24.000), False, True, False ),

Servico( con_pre_per, '2003319', Precisao().quantidade(522.000), False, False, False ),
Servico( con_pre_per, '2003377', Precisao().quantidade(3991.550), False, False, False ),
Servico( con_pre_per, '2003385', Precisao().quantidade(3.000), False, False, False ),
Servico( con_pre_per, '2003391', Precisao().quantidade(160.000), False, False, False ),
Servico( con_pre_per, '4011352', Precisao().quantidade(2400.000), False, False, False ),
Servico( con_pre_per, '4011353', Precisao().quantidade(170300.850), False, False, False ),
Servico( con_pre_per, '4011410', Precisao().quantidade(572796.000), False, False, False ),
Servico( con_pre_per, '4011463', Precisao().quantidade(20024.916), False, False, False ),
Servico( con_pre_per, '4915656', Precisao().quantidade(357.998), False, False, False ),
Servico( con_pre_per, '4915657', Precisao().quantidade(3937.973), False, False, False ),
Servico( con_pre_per, '4915662', Precisao().quantidade(327.312), False, False, False ),
Servico( con_pre_per, '4915663', Precisao().quantidade(3600.432), False, False, False ),

Servico( con_emerg, '1505860', Precisao().quantidade(12.434*2), False, False, False ),
Servico( con_emerg, '1505879', Precisao().quantidade(6.217*2), False, False, False ),
Servico( con_emerg, '1513940', Precisao().quantidade(994.528*2), False, False, False ),
Servico( con_emerg, '3205864', Precisao().quantidade(12.434*2), False, False, False ),
Servico( con_emerg, '3205866', Precisao().quantidade(12.434*2), False, False, False ),


Servico( dsm, '0605571', Precisao().quantidade(54.000), False, False, False ),
Servico( dsm, '0804401', Precisao().quantidade(2.000), False, False, False ),
Servico( dsm, '4011211', Precisao().quantidade(1200.000), False, False, False ),
Servico( dsm, '4011227', Precisao().quantidade(240.000), False, False, False ),
Servico( dsm, '4011287', Precisao().quantidade(240.000), False, False, False ),
Servico( dsm, '4011370', Precisao().quantidade(1200.000), False, False, False ),
Servico( dsm, '4011482', Precisao().quantidade(240.000), False, False, False ),
Servico( dsm, '4413996', Precisao().quantidade(2244.600), False, False, False ),
Servico( dsm, '4915667', Precisao().quantidade(60.000), False, False, False ),
Servico( dsm, '4915669', Precisao().quantidade(720.000), False, False, False ),

Servico( ser_aux_pre, '8888246', Precisao().quantidade(20024.916), True, False, False ),
Servico( ser_aux_pre, '8888254', Precisao().quantidade(20024.916), True, False, False ),
Servico( ser_aux_pre, '8888329', Precisao().quantidade(572796.000), True, False, False ),
Servico( ser_aux_pre, '8888339', Precisao().quantidade(170300.850), True, False, False ),
Servico( ser_aux_pre, '8888361', Precisao().quantidade(170300.850), True, False, False ),
Servico( ser_aux_pre, '8888371', Precisao().quantidade(572796.000), True, False, False ),
Servico( ser_aux_pre, '8888338', Precisao().quantidade(2400.000), True, False, False ),
Servico( ser_aux_pre, '8888362', Precisao().quantidade(2400.000), True, False, False ),
Servico( ser_aux_pre, '8888341', Precisao().quantidade(1200.000), True, False, False ),
Servico( ser_aux_pre, '8888359', Precisao().quantidade(1200.000), True, False, False ),

Servico( ser_aux_pre, '5214001', Precisao().quantidade(51142.500), False, False, False ),
Servico( ser_aux_rot, '5214011', Precisao().quantidade(1704.750), False, False, False ),

Servico( ser_aux_transp_pv, '5914344', Precisao().quantidade(138145.206), False, False, False ),
Servico( ser_aux_transp_pv, '5914366', Precisao().quantidade(58263.629), False, False, False ),
Servico( ser_aux_transp_pv, '5914389', Precisao().quantidade(5247281.091), False, False, False ),
Servico( ser_aux_transp_pv, '5914434', Precisao().quantidade(34879.904), False, False, False ),
Servico( ser_aux_transp_pv, '5914479', Precisao().quantidade(125312.535), False, False, False ),
Servico( ser_aux_transp_pv, '5914614', Precisao().quantidade(1378.485), False, False, False ),
Servico( ser_aux_transp_pv, '5915324', Precisao().quantidade(1441.905), False, False, False ),
Servico( ser_aux_transp_pv, '5914583', Precisao().quantidade(10910.400), False, False, False ),

Servico( ser_aux_transp_rp, '5914329', Precisao().quantidade(370.477), False, False, False ),
Servico( ser_aux_transp_rp, '5914365', Precisao().quantidade(116.375), False, False, False ),
Servico( ser_aux_transp_rp, '5914374', Precisao().quantidade(58395.402), False, False, False ),
Servico( ser_aux_transp_rp, '5914419', Precisao().quantidade(19.475), False, False, False ),
Servico( ser_aux_transp_rp, '5914464', Precisao().quantidade(552.796), False, False, False ),
Servico( ser_aux_transp_rp, '5914599', Precisao().quantidade(3.056), False, False, False ),
Servico( ser_aux_transp_rp, '5915323', Precisao().quantidade(11.432), False, False, False ),

Servico( sin_obra, '9999310', Precisao().quantidade(20.000), False, False, False ),
Servico( sin_obra, '9999320', Precisao().quantidade(20.000), False, False, False ),
Servico( sin_obra, '9999330', Precisao().quantidade(120.000), False, False, False ),
Servico( sin_obra, '9999340', Precisao().quantidade(45.000), False, False, False ),
Servico( sin_obra, '9999350', Precisao().quantidade(454.600), False, False, False ),

Servico( adm_loc, '9999106', Precisao().quantidade(2.000), False, True, False ),
Servico( can_ins, '0903810', Precisao().quantidade(1.000), False, True, False ),
Servico( can_ins, '9999400', Precisao().quantidade(1.000), False, True, False ),
Servico( mob_des, '9999500', Precisao().quantidade(1.000), False, False, False ),

]




situacao = False
if situacao:
    bdi = BonificacaoDespesasIndiretas( 0.3177, 0.1500, situacao )
else:
    bdi = BonificacaoDespesasIndiretas( 0.3850, 0.2124, situacao )
    
fit_projeto = 0.0193

projeto1 = Projeto( lista_servico_proj1, baseDF, bdi, fit_projeto )


DADOS_PROJETO1 = DadosProjeto(
                    unidade_federacao='GO',
                    rodovia='BR-010',
                    trecho_inicial='Entr GO-118(A) (DIV DF/GO)',
                    trecho_final='DIV GO/TO (Rio Paranã)',
                    subtrecho_inicial='Entr GO-118(A) (DIV DF/GO)',
                    subtrecho_final='Entr GO-118(B)/241 (Teresina de Goiás)',
                    segmento_inicial=0.0,
                    segmento_final=227.3,
                    snv_inicial='010BGO0090',
                    snv_final='010BGO0170',
                    versao_snv='202310A',
                    data_base=Data(1,2024),
                    situacao_complementar=situacao,
                )

arquivo1 = '-'.join( ('ORC_CBUQ_USINADO', DADOS_PROJETO1.unidade_federacao, DADOS_PROJETO1.snv, DADOS_PROJETO1.data_base.data_completa, DADOS_PROJETO1.situacao_complementar, Data().data_completa ) )

escrever_arquivo_excel( arquivo1, projeto1, baseDF.max_apr(), DADOS_PROJETO1 )