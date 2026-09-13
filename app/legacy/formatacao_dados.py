from datetime import datetime

import locale

class Precisao:
    
    def __init__( self ) -> None:
        self._01_algarismos = 1
        self._02_algarismos = 2
        self._03_algarismos = 3
        self._04_algarismos = 4
        self._05_algarismos = 5
        self._06_algarismos = 6
        self._08_algarismos = 8
        self._10_algarismos = 10

    def quantidade( self, valor: float ) -> float:
        return round( valor, self._03_algarismos )

    def custo( self, valor: float ) -> float:
        return round( valor, self._04_algarismos )

    def monetario( self, valor: float ) -> float:
        return round( valor, self._02_algarismos )

    def utilizacao( self, valor: float ) -> float:
        return round( valor, self._06_algarismos )

    def utilizacao_transporte( self, valor: float ) -> float:
        return round( valor, self._10_algarismos )

    def utilizacao_equipamento( self, valor: float ) -> float:
        return round( valor, self._10_algarismos )

    def utilizacao_material( self, valor: float ) -> float:
        return round( valor, self._10_algarismos )

    def utilizacao_mao_de_obra( self, valor: float ) -> float:
        return round( valor, self._10_algarismos )

    def percentual( self, valor: float ) -> float:
        return round( valor, self._06_algarismos )

class Data:

    def __init__( self, mes=0, ano=0 ):
        self.data = datetime.now()
        self.MES_COMPLETO = {
                1:'janeiro',
                2:'fevereiro',
                3:u'março',
                4:'abril',
                5:'maio',
                6:'junho',
                7:'julho',
                8:'agosto',
                9:'setembro',
                10:'outubro',
                11:'novembro',
                12:'dezembro'
            }
        self.MES = {
                1:'jan',
                2:'fev',
                3:'mar',
                4:'abr',
                5:'mai',
                6:'jun',
                7:'jul',
                8:'ago',
                9:'set',
                10:'out',
                11:'nov',
                12:'dez'
            }
        self.configurar_mes_ano( mes, ano )
        self.mes_completo = self.MES_COMPLETO[ self.mes ]
        self.mes_abreviado = self.MES[ self.mes ]
        self.data_completa = '{}-{}'.format( self.mes_completo, self.ano )
        self.data_abreviada = '{}-{}'.format( self.mes_abreviado, self.ano )

    def configurar_mes_ano( self, mes: int, ano: int ):
        if ( mes == 0 ) or ( ano == 0 ):
            self.mes = int( self.data.strftime("%m") )
            self.ano = self.data.strftime("%Y")
        else:
            self.mes = mes
            self.ano = ano


class DadosProjeto:

    def __init__( self,
                    unidade_federacao: str,
                    rodovia: str,
                    trecho_inicial: str,
                    trecho_final: str,
                    subtrecho_inicial: str,
                    subtrecho_final: str,
                    segmento_inicial: float,
                    segmento_final: float,
                    snv_inicial: str,
                    snv_final: str,
                    versao_snv: str,
                    data_base: str,
                    situacao_complementar: bool,
                ) -> None:
        self.unidade_federacao = unidade_federacao
        self.rodovia = rodovia
        self.trecho = self.configurar_inicial_final( trecho_inicial, trecho_final )
        self.subtrecho = self.configurar_inicial_final( subtrecho_inicial, subtrecho_final )
        self.segmento = self.configurar_segmento( segmento_inicial, segmento_final )
        self.snv = self.configurar_inicial_final( snv_inicial, snv_final )
        self.versao_snv = versao_snv
        self.data_base = data_base
        self.situacao_complementar = self.configurar_situacao( situacao_complementar )

    def configurar_inicial_final( self, inicial: str, final: str ) -> str:
        return '{} - {}'.format( inicial, final )

    def configurar_segmento( self, inicial: float, final: float ) -> str:
        return 'KM{} - KM{}'.format( str( inicial ), str( final ) )

    def configurar_situacao( self, situacao_complementar: bool ) -> str:
        descricao_complementar = 'ONERADO'
        if not situacao_complementar:
            descricao_complementar = 'DESONERADO'
        return descricao_complementar


class Formatacao:

    def __init__( self, writer ):
        self.modulo = 10
        self.workbook = writer.book
        self.dicionario_formatacao = dict()
        self.tipo_letra()
        self.dicionario_formatacao['italic'] = False
        self.dicionario_formatacao['bold'] = False
        self.dicionario_cor = {
                    'black' : '#000000',
                    'blue' : '#0000FF',
                    'brown' : '#800000',
                    'cyan' : '#00FFFF',
                    'green' : '#008000',
                    'lime' : '#00FF00',
                    'magenta' : '#FF00FF',
                    'navy' : '#000080',
                    'orange' : '#FF6600',
                    'pink' : '#FF00FF',
                    'purple' : '#800080',
                    'red' : '#FF0000',
                    'light-gray' : '#DCDCDC',
                    'dark-gray' : '#A9A9A9',
                    'light-blue' : '#B0C4DE',
                    'cinza-claro-dnit': '#BFC3C6',
                    'cinza-escuro-dnit': '#58636B',
                    'amarelo-escuro-dnit': '#FBBE5E',
                    'azul-escuro-dnit' : '#003770',
                    'azul-claro-dnit' : '#70b6ff',
                    'white' : 'white',
                    'yellow' : '#FFFF00',
                    }

    def tipo_letra( self ):
        self.dicionario_formatacao.update( {'font_name': 'Open sans'} )

    def tamanho_letra( self ):
        self.dicionario_formatacao.update( {'font_size': 14} )

    def alinhamento_centro( self ):
        self.dicionario_formatacao.update( {'align':'center'} )

    def alinhamento_esquerda( self ):
        self.dicionario_formatacao.update( {'align':'left'} )

    def alinhamento_direita( self ):
        self.dicionario_formatacao.update( {'align':'right'} )

    def linha_grade_superior( self ):
        self.dicionario_formatacao.update( {'top':1} )

    def linha_grade_inferior( self ):
        self.dicionario_formatacao.update( {'bottom':1} )

    def cor_letra( self, cor: str='black' ) -> bool:
        if cor in self.dicionario_cor:
            self.dicionario_formatacao.update( {'font_color': self.dicionario_cor[cor] } )
        else:
            self.dicionario_formatacao.update( {'font_color':'black'} )

    def cor_fundo( self, cor: str='white' ):
        if cor in self.dicionario_cor:
            self.dicionario_formatacao.update( {'bg_color': self.dicionario_cor[cor] } )
        else:
            self.dicionario_formatacao.update( {'bg_color':'white'} )

    def algarismo_percentual( self ):
        representacao_valor = '0.000%'
        self.dicionario_formatacao.update( {'num_format': representacao_valor} )

    def algarismo_significativo( self, numero: int):
        representacao_valor = '###,###,###,##0'
        if numero > 0:
            representacao_valor = representacao_valor + '.'
            while numero > 0:
                representacao_valor = representacao_valor + '0'
                numero -= 1
        self.dicionario_formatacao.update( {'num_format': representacao_valor} )

    def negrito( self ):
        if self.dicionario_formatacao['bold'] == True:
            valor = False
        else:
            valor = True
        self.dicionario_formatacao.update( {'bold': valor} )

    def italico( self ):
        if self.dicionario_formatacao['italic'] == True:
            valor = False
        else:
            valor = True
        self.dicionario_formatacao.update( {'italic': valor} )

    def aplicar_formatacao( self ):
        return self.workbook.add_format( self.dicionario_formatacao )


class ConfiguraDataFrame:

    def __init__( self, data_frame, formatacao, linha_inicio=0 ):
        self.dfr = data_frame
        self.configurar_indice_iniciando_com_um()
        self.dfr.to_excel( formatacao.writer, startrow=( linha_inicio ), sheet_name=formatacao.nome_tabela, index=True )

    def configurar_indice_iniciando_com_um( self ):
        self.dfr['Item'] = [ x for x in range( 1, len( self.dfr ) + 1 ) ]
        self.dfr.set_index('Item', drop=True, inplace=True)

    def obter_data_frame_configurado( self ):
        return self.dfr


class Escrita:

    def __init__( self, formatacao, dados_projeto: DadosProjeto, tamanho, numero_de_composicoes=0 ):
        self.writer = formatacao.writer
        self.formatacao = formatacao
        self.nome_tabela = self.formatacao.nome_tabela
        self.entrada_area_de_impressao = self.formatacao.entrada_area_de_impressao
        self.dados_projeto = dados_projeto
        self.tamanho = tamanho + 1
        self.numero_de_composicoes = numero_de_composicoes

    def configurar_area_impressao( self ):
        area_de_impressao = self.entrada_area_de_impressao.format(1, self.tamanho )
        self.writer.sheets[ self.nome_tabela ].print_area( area_de_impressao )

    def configurar_escala_para_largura_pagina( self ):
        if self.numero_de_composicoes > 0:
            self.writer.sheets[ self.nome_tabela ].set_margins(top=3.0)
            self.configurar_cabecalho()
            self.configurar_rodape()
            # self.writer.sheets[ self.nome_tabela ].set_print_scale(27)
            self.writer.sheets[ self.nome_tabela ].fit_to_pages(1, self.numero_de_composicoes)
        else:
            self.writer.sheets[ self.nome_tabela ].set_margins(top=2.0)
            # self.writer.sheets[ self.nome_tabela ].set_print_scale(50)
            self.configurar_cabecalho()
            self.configurar_rodape()
            self.configurar_repeticao_primeira_linha_tabela()
            self.configurar_linhas_de_grade()
        
    def configurar_orientacao_papel( self ):
        if self.formatacao.orientacao_retrato == True:
            self.writer.sheets[ self.nome_tabela ].set_portrait()
        else:
            self.writer.sheets[ self.nome_tabela ].set_landscape()

    def configurar_papel_a4( self ):
        # índice 9 (papel A4) vem da documentação da biblioteca xlsxwriter
        self.writer.sheets[ self.nome_tabela ].set_paper(9)

    def configurar_tabela_centro_pagina( self ):
        self.writer.sheets[ self.nome_tabela ].center_horizontally()

    def configurar_repeticao_primeira_linha_tabela( self ):
        self.writer.sheets[ self.nome_tabela ].repeat_rows(0)

    def configurar_formatacao_coluna_tabela( self ):
        for obj_entrada in self.formatacao.lista_entrada_formatacao:
            self.writer.sheets[ self.nome_tabela ].set_column( obj_entrada.coluna, obj_entrada.largura, obj_entrada.formatado )

    def configurar_linhas_de_grade( self ):
        self.writer.sheets[ self.nome_tabela ].hide_gridlines(option=0)

    def configurar_cabecalho( self ):
        sigla = 'DNIT'
        sigla_formatada = '"Arial Black, Bold, Italic"&36&K003770{}\n'.format( sigla )
        guia = 'A'
        guia_formatada = '"Open sans"&14&K003770&{}\n'.format( guia )
        rodovia = self.dados_projeto.rodovia
        trecho = self.dados_projeto.trecho
        subtrecho = self.dados_projeto.subtrecho
        versao = self.dados_projeto.versao_snv
        objeto = '{}\n{}\n{}\n ({})'.format( rodovia, trecho, subtrecho, versao )
        objeto_formatado = '"Open sans"&12&K003770{}\n'.format( objeto )
        cabecalho = '&L&{}&C&{}&L&{}'.format( sigla_formatada, guia_formatada, objeto_formatado )
        self.writer.sheets[ self.nome_tabela ].set_header( cabecalho, {'scale_with_doc': False} )

    def configurar_rodape( self ):
        agora = Data()
        data_base = self.dados_projeto.data_base
        situacao_complementar = self.dados_projeto.situacao_complementar
        conteudo_rodape = '&C&"Open sans"&11&K003770data base {} ({})\ncalculado em {}'.format( data_base.data_completa, situacao_complementar, agora.data_completa )
        self.writer.sheets[ self.nome_tabela ].set_footer( conteudo_rodape, {'scale_with_doc': False})

    def obter_escritor_configurado( self ):
        self.configurar_area_impressao()
        self.configurar_escala_para_largura_pagina()
        self.configurar_orientacao_papel()
        self.configurar_papel_a4()
        self.configurar_tabela_centro_pagina()
        self.configurar_formatacao_coluna_tabela()
        return self.writer


class EscritaCabecalho:

    def __init__( self, formatacao, linha_inicio ):
        self.writer = formatacao.writer
        self.formatacao = formatacao
        self.nome_tabela = formatacao.nome_tabela
        self.lista_entrada_formatacao = formatacao.lista_entrada_formatacao
        self.linha_inicio = linha_inicio

    def configurar_cabecalho( self ):
        for obj_entrada in self.lista_entrada_formatacao:
            self.writer.sheets[ self.formatacao.nome_tabela ].write( ''.join( ( obj_entrada.coluna, str(self.linha_inicio)) ), obj_entrada.conteudo, obj_entrada.formatado )

    def obter_escritor_configurado( self ):
        self.configurar_cabecalho()
        return self.writer


class Grupo:

    def __init__( self ) -> None:
        self.composicao_principal = 10
        self.linha_vazia_inicial = 19
        self.insumo_equipamento = 20
        self.subtotal_horario_equipamento = 22
        self.linha_vazia_equipamento = 29
        self.insumo_mao_de_obra = 30
        self.subtotal_horario_mao_de_obra = 32
        self.linha_vazia_mao_de_obra = 33
        self.subtotal_execucao = 34
        self.subtotal_unitario_execucao = 35
        self.subtotal_unitario_fic = 36
        self.subtotal_unitario_fit = 37
        self.linha_vazia_execucao = 39
        self.insumo_material = 40
        self.subtotal_unitario_material = 42
        self.linha_vazia_material = 49
        self.insumo_atividade_auxiliar = 50
        self.subtotal_unitario_atividade_auxiliar = 52
        self.linha_vazia_atividade_auxiliar = 59
        self.insumo_tempo_fixo = 60
        self.subtotal_unitario_tempo_fixo = 62
        self.linha_vazia_tempo_fixo = 69
        self.insumo_transporte = 70
        self.insumo_tr_ln = 74
        self.insumo_tr_rp = 75
        self.insumo_tr_pv = 76
        self.insumo_tr_fe = 77
        self.subtotal_unitario_transporte = 78
        self.linha_vazia_transporte = 79
        self.total_unitario_direto = 80
        self.linha_vazia_unitario_direto = 81
        self.subtotal_unitario_bdi = 90
        self.linha_vazia_bdi = 99
        self.total_preco_unitario = 100


class Codigo:

    def __init__( self ) -> None:
        self.horario = 'ho'
        self.execucao = 'ex'
        self.unitario = 'un'
        self.direto_total = 'dt'
        self.preco_unitario = 'pu'


class ListaColuna:

    def __init__( self ) -> None:
        self.codigo = 'Código'
        self.composicao_principal = 'Composição'
        self.servico_orcamento = 'Serviço orçamento'
        self.grupo = 'Grupo'
        self.descricao = 'Descrição'
        self.item_transporte = 'Item transportado'
        self.preco_unitario = 'Preço unitário'
        self.quantidade = 'Quantidade'
        self.quantidade_hora_produtiva = 'Quantidade produtiva'
        self.quantidade_hora_improdutiva = 'Quantidade improdutiva'
        self.quantidade_hora_total = 'Quantidade hora total'
        self.utilizacao_produtiva = 'Utilização produtiva'
        self.utilizacao_improdutiva = 'Utilização improdutiva'
        self.unidade = 'Unidade'
        self.utilizacao = 'Utilização'
        self.custo_unitario_total = 'Custo unitário total'
        self.custo_total = 'Custo total'
        self.dmt = 'DMT'
        self.dmt_ln = 'DMT LN'
        self.dmt_rp = 'DMT RP'
        self.dmt_pv = 'DMT PV'
        self.dmt_fe = 'DMT FE'
        self.estado = 'Estado'
        self.fic = 'FIC'
        self.produtividade = 'Produtividade'
        self.publicacao = 'Publicação'
        self.tipo = 'Tipo'
        self.origem = 'Origem'
        self.custo_imp_desonerado = 'Custo improdutivo desonerado'
        self.custo_imp_onerado = 'Custo improdutivo onerado'
        self.custo_improdutivo = 'Custo improdutivo'
        self.custo_pro_desonerado = 'Custo produtivo desonerado'
        self.custo_pro_onerado = 'Custo produtivo onerado'
        self.custo_produtivo = 'Custo produtivo'
        self.momento_transporte_unitario = 'Momento transporte unitário'
        self.momento_transporte_total = 'Momento transporte total'
        self.percentual_total = 'Percentual do total'
        self.percentual_acumulado = 'Percentual acumulado'


    def configurar_custo_produtivo( self, onerado: bool ) -> str:
        if onerado:
            situacao = self.custo_pro_onerado
        else:
            situacao = self.custo_pro_desonerado
        return situacao

    def configurar_custo_improdutivo( self, onerado: bool ) -> str:
        if onerado:
            situacao = self.custo_imp_onerado
        else:
            situacao = self.custo_imp_desonerado
        return situacao


class ListaColunaOrigemCP(ListaColuna):

    def __init__( self ) -> None:
        super().__init__()

    def obter_lista( self ) -> list:
        return [
                    self.origem,
                    self.estado,
                    self.publicacao
                ]


class ListaColunaComposicaoDB(ListaColuna):

    def __init__( self ) -> None:
        super().__init__()

    def obter_lista( self ) -> list:
        return [
                    self.composicao_principal,
                    self.fic,
                    self.produtividade,
                    self.tipo,
                ]


class ListaColunaInsumoDB(ListaColuna):

    def __init__( self ) -> None:
        super().__init__()

    def obter_lista( self ) -> list:
        return [
                    self.codigo,
                    self.descricao,
                    self.unidade,
                ]


class ListaColunaApropriacaoDB(ListaColuna):

    def __init__( self ) -> None:
        super().__init__()

    def obter_lista( self ) -> list:
        return [
                    self.composicao_principal,
                    self.codigo,
                    self.quantidade,
                    self.utilizacao,
                    self.item_transporte,
                    self.grupo,
                ]


class ListaColunaDMTInsumoDB(ListaColuna):

    def __init__( self ) -> None:
        super().__init__()

    def obter_lista( self ) -> list:
        return [ 
                    self.item_transporte,
                    self.dmt_ln,
                    self.dmt_rp,
                    self.dmt_pv,
                    self.dmt_fe,
                ]


class ListaColunaCustoInsumoCT(ListaColuna):

    def __init__( self ) -> None:
        super().__init__()

    def obter_lista( self ) -> list:
        return [ 
                    self.codigo,
                    self.custo_pro_onerado,
                    self.custo_imp_onerado,
                    self.custo_pro_desonerado,
                    self.custo_imp_desonerado,
                    self.preco_unitario,
                    self.grupo,
                ]


class ListaColunaComposicaoDF(ListaColuna):

    def __init__( self, onerado: bool ) -> None:
        super().__init__()
        self.custo_produtivo = self.configurar_custo_produtivo( onerado )
        self.custo_improdutivo = self.configurar_custo_improdutivo( onerado )

    def obter_lista( self ) -> list:
        return [ 
                    self.composicao_principal,
                    self.grupo,
                    self.codigo,
                    self.descricao,
                    self.item_transporte,
                    self.dmt,
                    self.unidade,
                    self.quantidade,
                    self.utilizacao,
                    self.custo_produtivo,
                    self.custo_improdutivo,
                    self.preco_unitario,
                    self.custo_total
                ]