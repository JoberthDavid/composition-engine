import unittest
import numpy as np
import pandas as pd

from projeto import (
                    GeradorDF,
                    ComposicaoStr,
                    BaseDF,
                    BonificacaoDespesasIndiretas,
                    ComposicaoDB,
                    ComposicaoDF,
                    LinhaDF,
                    LinhaEquipamentoDF,
                    LinhaMaoDeObraDF,
                    LinhaMaterialDF,
                    LinhaCustoHorarioExecucaoDF,
                    LinhaCustoUnitarioExecucaoDF,
                    LinhaAtividadeAuxiliarDF,
                    LinhaTempoFixoDF,
                    LinhaTransporteDF,
                    LinhaCustoUnitarioDiretoTotalDF
                )
from formatacao_dados import (
                    Precisao,
                    Grupo,
                    Codigo,
                    ListaColuna,
                    ListaColunaOrigemCP,
                    ListaColunaComposicaoDB,
                    ListaColunaInsumoDB,
                    ListaColunaApropriacaoDB,
                    ListaColunaCustoInsumoCT,
                    ListaColunaComposicaoDF,
                )
from arquivos import arq_db_cp, arq_db_in, arq_apr_in, arq_cto_in

codigo_composicao_1 = str(307731)
codigo_composicao_2 = str(4011287)
bdi_principal = 0.267
bdi_diferenciado = 0.150
onerado = True
fit_projeto = 0.0735

class TestGeradorDF(unittest.TestCase):

    def setUp( self ):
        self.obj_GeradorDF = GeradorDF( arq_db_cp )

    def test_create_GeradorDF( self ):
        self.assertIsInstance( self.obj_GeradorDF, GeradorDF )

class TestComposicaoStr(unittest.TestCase):

    def setUp( self ):
        self.obj_ComposicaoStr = ComposicaoStr( codigo_composicao_1 )

    def test_create_ComposicaoStr( self ):
        self.assertIsInstance( self.obj_ComposicaoStr, ComposicaoStr )

    def test_result_of_ComposicaoStr( self ):
        self.assertEqual( len(self.obj_ComposicaoStr.codigo), 7 )
        self.assertIsInstance( self.obj_ComposicaoStr.codigo, str )

class TestBaseDF(unittest.TestCase):

    def setUp( self ):
        self.obj_BaseDF = BaseDF( arq_db_cp, arq_db_in, arq_apr_in, arq_cto_in )
        self.obj_col_db_cp = ListaColunaComposicaoDB()
        self.obj_col_db_in = ListaColunaInsumoDB()
        self.obj_col_db_ap = ListaColunaApropriacaoDB()
        self.obj_col_ct_in = ListaColunaCustoInsumoCT()

    def test_instance_of_BaseDF( self ):
        self.assertIsInstance( self.obj_BaseDF, BaseDF )

    def test_instance_of_carregar_df( self ):
        self.assertIsInstance( self.obj_BaseDF.dfr_dados_cp, pd.core.frame.DataFrame )

    def test_result_of_tratar_dfr_dados_basicos_cp( self ):
        obj_GeradorDF = GeradorDF( arq_db_cp )
        lista_colunas_dfr_dados_cp = obj_GeradorDF.tratar_dfr( self.obj_col_db_cp.obter_lista() ).columns
        self.assertEqual( len( self.obj_BaseDF.dfr_dados_cp.columns.values ), len( lista_colunas_dfr_dados_cp.values ) )

    def test_result_of_tratar_dfr_dados_basicos_in( self ):
        dfr_db_in = GeradorDF( arq_db_in )
        lista_colunas_dfr_db_in = dfr_db_in.tratar_dfr( self.obj_col_db_in.obter_lista() ).columns
        self.assertEqual( len( self.obj_BaseDF.dfr_dados_in.columns.values ), len( lista_colunas_dfr_db_in.values ) )

    def test_result_of_tratar_dfr_apropriacao_in( self ):
        dfr_apr_in = GeradorDF( arq_apr_in )
        lista_colunas_dfr_apr_in = dfr_apr_in.tratar_dfr( self.obj_col_db_ap.obter_lista() ).columns
        self.assertEqual( len( self.obj_BaseDF.dfr_apropriacao_in.columns.values ), len( lista_colunas_dfr_apr_in.values ) )

    def test_result_of_tratar_dfr_custo_in( self ):
        dfr_cto_in = GeradorDF( arq_cto_in )
        lista_colunas_dfr_cto_in = dfr_cto_in.tratar_dfr( self.obj_col_ct_in.obter_lista() ).columns
        self.assertEqual( len( self.obj_BaseDF.dfr_custo_in.columns.values ), len( lista_colunas_dfr_cto_in.values ) )


class TestBonificacaoDespesasIndiretas(unittest.TestCase):

    def setUp( self ):
        self.obj_BDI = BonificacaoDespesasIndiretas( bdi_principal, bdi_diferenciado, onerado )
        self.onerado = onerado

    def test_attribute_of_bdi( self ):
        self.assertEqual( self.obj_BDI.principal, bdi_principal )
        self.assertEqual( self.obj_BDI.diferenciado, bdi_diferenciado )
        self.assertEqual( self.obj_BDI.onerado, self.onerado )


class TestComposicaoDB(unittest.TestCase):

    def setUp( self ):
        self.obj_BDI = BonificacaoDespesasIndiretas( bdi_principal, bdi_diferenciado, onerado=True)
        self.obj_ComposicaoDB = ComposicaoDB( codigo_composicao_1, self.obj_BDI, fit_projeto, diferenciado=False )
        self.obj_ComposicaoDB.descricao = 'Base de solo melhorado com 4% de cimento e mistura na pista com material de jazida'
        self.obj_ComposicaoDB.unidade = 'm³'
        self.obj_ComposicaoDB.fic = 0.03149
        self.obj_ComposicaoDB.produtividade  = 146.23000
        self.obj_ComposicaoDB.custo_horario_equipamento = 655.3187
        self.obj_ComposicaoDB.custo_horario_mao_de_obra = 90.6054
        self.obj_ComposicaoDB.custo_execucao = 745.9241
        self.obj_ComposicaoDB.custo_unitario_execucao = 5.1010
        self.obj_ComposicaoDB.custo_unitario_material = 39.2218
        self.obj_ComposicaoDB.custo_total_insumos = 44.4834
        self.obj_ComposicaoDB.custo_total_atividade_auxiliar = 1.0457
        self.obj_ComposicaoDB.custo_total_tempo_fixo = 3.7588
        self.obj_ComposicaoDB.custo_total_transporte = 0.0000
        self.obj_ComposicaoDB.custo_unitario_total = 49.29
        self.obj_ComposicaoDB.custo_bdi = 0.0000
        self.obj_ComposicaoDB.preco_unitario_total = 49.29
        self.obj_precisao = Precisao()

    def test_instance_of_ComposicaoDB( self ):
        self.assertIsInstance( self.obj_ComposicaoDB, ComposicaoDB )
    
    def test_result_of_calcular_custo_execucao( self ):
        resultado = round( self.obj_ComposicaoDB.custo_horario_equipamento + self.obj_ComposicaoDB.custo_horario_mao_de_obra, self.obj_precisao._04_algarismos )
        esperado = self.obj_ComposicaoDB.configurar_custo_execucao()
        self.assertEqual( resultado, esperado )
        self.assertIsInstance( resultado, float )

    def test_result_of_calcular_custo_unitario_execucao( self ):
        resultado = round( self.obj_ComposicaoDB.configurar_custo_unitario_execucao(), self.obj_precisao._04_algarismos )
        esperado = self.obj_ComposicaoDB.custo_unitario_execucao
        self.assertEqual( resultado, esperado )
        self.assertIsInstance( resultado, float )

    def test_result_of_calcular_custo_fic( self ):
        resultado = round(  self.obj_ComposicaoDB.configurar_custo_fic(), self.obj_precisao._04_algarismos )
        esperado = self.obj_ComposicaoDB.custo_fic
        self.assertEqual( resultado, esperado )
        self.assertIsInstance( resultado, float )

    def test_result_of_calcular_custo_fit( self ):
        resultado = round(  self.obj_ComposicaoDB.configurar_custo_fit(), self.obj_precisao._04_algarismos )
        esperado = self.obj_ComposicaoDB.custo_fit
        self.assertEqual( resultado, esperado )
        self.assertIsInstance( resultado, float )

    def test_result_of_calcular_bdi( self ):
        resultado = round( self.obj_ComposicaoDB.configurar_custo_bdi() , self.obj_precisao._02_algarismos )
        esperado = self.obj_ComposicaoDB.custo_bdi
        self.assertEqual( resultado, esperado )
        self.assertIsInstance( resultado, float )

    def test_result_of_calcular_custo_unitario_total( self ):
        custo_insumos = self.obj_ComposicaoDB.custo_unitario_execucao + self.obj_ComposicaoDB.custo_unitario_material
        custo_servicos = self.obj_ComposicaoDB.custo_fic + self.obj_ComposicaoDB.custo_fit + self.obj_ComposicaoDB.custo_total_atividade_auxiliar + self.obj_ComposicaoDB.custo_total_tempo_fixo + self.obj_ComposicaoDB.custo_total_transporte
        resultado = round( custo_insumos + custo_servicos, self.obj_precisao._02_algarismos )
        esperado = self.obj_ComposicaoDB.configurar_custo_unitario_total()
        self.assertEqual( resultado, esperado )
        self.assertIsInstance( resultado, float )

    def test_result_of_calcular_preco_unitario_total( self ):
        resultado = round( self.obj_ComposicaoDB.custo_bdi + self.obj_ComposicaoDB.custo_unitario_total, self.obj_precisao._02_algarismos )
        esperado = self.obj_ComposicaoDB.configurar_preco_unitario_total()
        self.assertEqual( resultado, esperado )
        self.assertIsInstance( resultado, float )


class TestComposicaoDF(unittest.TestCase):

    def setUp( self ):
        obj_BDI = BonificacaoDespesasIndiretas(bdi_principal, bdi_diferenciado, onerado=True)
        obj_ComposicaoDB = ComposicaoDB( codigo_composicao_2, obj_BDI, fit_projeto, diferenciado=False )
        obj_BaseDF = BaseDF( arq_db_cp, arq_db_in, arq_apr_in, arq_cto_in )
        self.obj_ComposicaoDF = ComposicaoDF( obj_ComposicaoDB, obj_BaseDF )
        self.obj_precisao = Precisao()
        self.obj_col_dfr = ListaColunaComposicaoDF( obj_ComposicaoDB.onerado )
        self.obj_grupo = Grupo()
        self.obj_codigo = Codigo()

    def test_instance_of_ComposicaoDF( self ):
        self.assertIsInstance( self.obj_ComposicaoDF, ComposicaoDF )

    def test_result_and_instance_of_obter_dfr_dados_basicos_insumos( self ):
        resultado = self.obj_ComposicaoDF.obter_dfr_dados_basicos_insumos()
        esperado = self.obj_ComposicaoDF.base.dfr_dados_in.query( "{} == '{}'".format( self.obj_col_dfr.codigo, self.obj_ComposicaoDF.composicao.codigo ) )
        pd._testing.assert_frame_equal( resultado, esperado )
        self.assertIsInstance( resultado, pd.core.frame.DataFrame )

    def test_result_and_instance_of_obter_dfr_dados_basicos_composicao( self ):
        resultado = self.obj_ComposicaoDF.obter_dfr_dados_basicos_composicao()
        esperado = self.obj_ComposicaoDF.base.dfr_dados_cp.query( "{} == '{}'".format( self.obj_col_dfr.composicao_principal, self.obj_ComposicaoDF.composicao.codigo ) )
        pd._testing.assert_frame_equal( resultado, esperado )
        self.assertIsInstance( resultado, pd.core.frame.DataFrame )

    def test_result_and_instance_of_obter_dfr_apropriacoes_insumos( self ):
        resultado = self.obj_ComposicaoDF.obter_dfr_apropriacoes_insumos()
        esperado = self.obj_ComposicaoDF.base.dfr_apropriacao_in.query( "{} == '{}'".format( self.obj_col_dfr.composicao_principal,self.obj_ComposicaoDF.composicao.codigo ) )
        pd._testing.assert_frame_equal( resultado, esperado )
        self.assertIsInstance( resultado, pd.core.frame.DataFrame )

    def test_result_and_instance_of_obter_descricao_composicao( self ):
        resultado = self.obj_ComposicaoDF.obter_descricao_composicao()
        esperado = self.obj_ComposicaoDF.composicao.descricao
        self.assertEqual( resultado, esperado )
        self.assertIsInstance( resultado, str )

    def test_result_and_instance_of_obter_unidade_composicao( self ):
        resultado = self.obj_ComposicaoDF.obter_unidade_composicao()
        esperado = self.obj_ComposicaoDF.composicao.unidade
        self.assertEqual( resultado, esperado )
        self.assertIsInstance( resultado, str )

    def test_result_and_instance_of_obter_fic_composicao( self ):
        resultado = self.obj_ComposicaoDF.obter_fic_composicao()
        esperado = self.obj_ComposicaoDF.composicao.fic
        self.assertEqual( resultado, esperado )
        self.assertIsInstance( resultado, float )
    
    def test_result_and_instance_of_obter_produtividade_composicao( self ):
        resultado = self.obj_ComposicaoDF.obter_produtividade_composicao()
        esperado = self.obj_ComposicaoDF.composicao.produtividade
        self.assertEqual( resultado, esperado )
        self.assertIsInstance( resultado, float )

    def test_instance_of_obter_dados_basicos_apropriacoes_insumos( self ):
        resultado = self.obj_ComposicaoDF.associar_dfr_dados_basicos_apropriacoes_insumos()
        self.assertIsInstance( resultado, pd.core.frame.DataFrame )

    def test_result_and_instance_of_obter_desoneracao_mao_de_obra( self ):
        resultado = self.obj_ComposicaoDF.composicao.onerado
        self.assertEqual( resultado, True)
        self.assertIsInstance( resultado, bool )
       
    def test_result_and_instance_of_obter_descricao_custo_produtivo( self ):
        resultado = self.obj_col_dfr.custo_pro_onerado
        esperado = self.obj_ComposicaoDF.obj_col_dfr.custo_produtivo
        self.assertEqual( resultado, esperado )
        self.assertIsInstance( resultado, str )

    def test_result_of_obter_descricao_custo_improdutivo( self ):
        resultado = self.obj_col_dfr.custo_imp_onerado
        esperado = self.obj_ComposicaoDF.obj_col_dfr.custo_improdutivo
        self.assertEqual( resultado, esperado )
    
    def test_result_of_inserir_cl_dmt( self ):
        self.obj_ComposicaoDF.inserir_col_dmt()
        resultado = self.obj_ComposicaoDF.dfr_insumo[self.obj_ComposicaoDF.obj_col_dfr.dmt].to_list()
        esperado = ['','','','','','','','','','','','','','','','','','','','','','','','']
        self.assertListEqual( resultado, esperado )

    def test_result_of_obter_lis_colunas( self ):
        resultado = self.obj_ComposicaoDF.obj_col_dfr.obter_lista()
        esperado = [self.obj_ComposicaoDF.obj_col_dfr.composicao_principal, self.obj_ComposicaoDF.obj_col_dfr.grupo, self.obj_ComposicaoDF.obj_col_dfr.codigo, self.obj_ComposicaoDF.obj_col_dfr.descricao, self.obj_ComposicaoDF.obj_col_dfr.item_transporte, self.obj_ComposicaoDF.obj_col_dfr.dmt, self.obj_ComposicaoDF.obj_col_dfr.unidade, self.obj_ComposicaoDF.obj_col_dfr.quantidade, self.obj_ComposicaoDF.obj_col_dfr.utilizacao, self.obj_ComposicaoDF.obj_col_dfr.custo_produtivo , self.obj_ComposicaoDF.obj_col_dfr.custo_improdutivo, self.obj_ComposicaoDF.obj_col_dfr.preco_unitario, self.obj_ComposicaoDF.obj_col_dfr.custo_total]
        self.assertListEqual( resultado, esperado )

    def test_result_of_associar_dfr_custos_apropriacoes_insumos( self ):
        resultado = self.obj_ComposicaoDF.associar_dfr_custos_apropriacoes_insumos()
        esperado = pd.merge( self.obj_ComposicaoDF.associar_dfr_dados_basicos_apropriacoes_insumos(), self.obj_ComposicaoDF.dfr_custo_in, on=self.obj_col_dfr.codigo, how='left', suffixes=[None,'_y'] )
        pd._testing.assert_frame_equal( resultado, esperado )
    
    def test_result_of_calcular_sre_custo_equipamento( self ):
        resultado = 0
        for composicao, _dfr_insumo in self.obj_ComposicaoDF.dfr_insumo.groupby( [self.obj_col_dfr.composicao_principal, self.obj_ComposicaoDF.obj_col_dfr.grupo] ):
            if composicao[1] == self.obj_grupo.insumo_equipamento : 
              resultado = _dfr_insumo[ self.obj_col_dfr.custo_total ].sum()
        esperado = self.obj_ComposicaoDF.composicao.custo_horario_equipamento
        self.assertEqual( resultado, esperado )

    def test_result_of_calcular_sre_custo_mao_de_obra( self ):
        resultado = 0
        for composicao, _dfr_insumo in self.obj_ComposicaoDF.dfr_insumo.groupby( [ self.obj_col_dfr.composicao_principal, self.obj_ComposicaoDF.obj_col_dfr.grupo] ):
            if composicao[1] == self.obj_grupo.insumo_mao_de_obra :
              resultado = _dfr_insumo[ self.obj_col_dfr.custo_total ].sum()
        esperado = self.obj_ComposicaoDF.composicao.custo_horario_mao_de_obra
        self.assertEqual( resultado, esperado )
        
    def test_result_of_calcular_sre_custo_material( self ):
        resultado = 0
        for composicao, _dfr_insumo in self.obj_ComposicaoDF.dfr_insumo.groupby( [ self.obj_col_dfr.composicao_principal, self.obj_ComposicaoDF.obj_col_dfr.grupo] ):
            if composicao[1] == self.obj_grupo.insumo_material :
              resultado = _dfr_insumo[ self.obj_col_dfr.custo_total ].sum()
        esperado = self.obj_ComposicaoDF.composicao.custo_unitario_material
        self.assertEqual( resultado, esperado )

    def test_result_of_obter_dfr_custo_equipamento( self ):
        resultado = self.obj_ComposicaoDF.dfr_insumo.query( '{} == {}'.format(self.obj_ComposicaoDF.obj_col_dfr.grupo, self.obj_grupo.insumo_equipamento ) )
        esperado = [169.9741, 2.0144, 165.7011, 126.1242, 127.226, 84.5544]
        self.assertListEqual( resultado[ self.obj_col_dfr.custo_total ].to_list(), esperado )
    
    def test_result_of_obter_dfr_custo_mao_de_obra( self ):
        resultado = self.obj_ComposicaoDF.dfr_insumo.query( '{} == {}'.format(self.obj_ComposicaoDF.obj_col_dfr.grupo, self.obj_grupo.insumo_mao_de_obra ) )
        esperado = [95.5608]
        self.assertListEqual( resultado[ self.obj_col_dfr.custo_total ].to_list(), esperado )

    def test_result_of_obter_dfr_custo_material( self ):
        resultado = self.obj_ComposicaoDF.dfr_insumo.query( '{} == {}'.format(self.obj_ComposicaoDF.obj_col_dfr.grupo, self.obj_grupo.insumo_material ) )
        esperado = [24.5580]
        self.assertListEqual( resultado[ self.obj_col_dfr.custo_total ].to_list(), esperado )

    def test_result_of_obter_dfr_equipamento( self ):
        resultado = self.obj_ComposicaoDF.obter_dfr_equipamento()
        esperado = self.obj_ComposicaoDF.dfr_insumo.query( '{} == {}'.format(self.obj_ComposicaoDF.obj_col_dfr.grupo, self.obj_grupo.insumo_equipamento ) )
        pd._testing.assert_frame_equal( resultado, esperado )

    def test_result_of_obter_dfr_mao_de_obra( self ):
        resultado = self.obj_ComposicaoDF.obter_dfr_mao_de_obra()
        esperado = self.obj_ComposicaoDF.dfr_insumo.query( '{} == {}'.format(self.obj_ComposicaoDF.obj_col_dfr.grupo, self.obj_grupo.insumo_mao_de_obra ) )
        pd._testing.assert_frame_equal( resultado, esperado )

    def test_result_of_obter_dfr_material( self ):
        resultado = self.obj_ComposicaoDF.obter_dfr_material()
        esperado = self.obj_ComposicaoDF.dfr_insumo.query( '{} == {}'.format(self.obj_ComposicaoDF.obj_col_dfr.grupo, self.obj_grupo.insumo_material ) )
        pd._testing.assert_frame_equal( resultado, esperado )

    def test_instance_of_criar_linha_subtotal_equipamento( self ):
        _dfr_insumo = self.obj_ComposicaoDF.obter_dfr_equipamento()
        resultado = self.obj_ComposicaoDF.criar_linha_subtotal_equipamento( _dfr_insumo, self.obj_ComposicaoDF.composicao, self.obj_ComposicaoDF.obj_col_dfr )
        self.assertIsInstance( resultado, LinhaEquipamentoDF)

    def test_instance_of_criar_linha_subtotal_mao_de_obra( self ):
        _dfr_insumo = self.obj_ComposicaoDF.obter_dfr_mao_de_obra()
        resultado = self.obj_ComposicaoDF.criar_linha_subtotal_mao_de_obra( _dfr_insumo, self.obj_ComposicaoDF.composicao, self.obj_ComposicaoDF.obj_col_dfr )
        self.assertIsInstance( resultado, LinhaMaoDeObraDF)

    def test_instance_of_criar_linha_subtotal_material( self ):
        _dfr_insumo = self.obj_ComposicaoDF.obter_dfr_material()
        resultado = self.obj_ComposicaoDF.criar_linha_subtotal_material( _dfr_insumo, self.obj_ComposicaoDF.composicao, self.obj_ComposicaoDF.obj_col_dfr )
        self.assertIsInstance( resultado, LinhaMaterialDF)

    def test_instance_of_criar_linha_custo_horario_execucao( self ):
        _dfr_insumo = self.obj_ComposicaoDF.dfr_insumo.query( '{} == {}'.format(self.obj_ComposicaoDF.obj_col_dfr.grupo, self.obj_grupo.subtotal_execucao ) )
        resultado = self.obj_ComposicaoDF.criar_linha_custo_execucao( _dfr_insumo, self.obj_ComposicaoDF.composicao, self.obj_ComposicaoDF.obj_col_dfr )
        self.assertIsInstance( resultado, LinhaCustoHorarioExecucaoDF)

    def test_instance_of_criar_linha_custo_unitario_execucao( self ):
        _dfr_insumo = self.obj_ComposicaoDF.dfr_insumo.query( '{} == {}'.format(self.obj_ComposicaoDF.obj_col_dfr.grupo, self.obj_grupo.subtotal_unitario_execucao ) )
        resultado = self.obj_ComposicaoDF.criar_linha_custo_unitario_execucao( _dfr_insumo, self.obj_ComposicaoDF.composicao, self.obj_ComposicaoDF.obj_col_dfr )
        self.assertIsInstance( resultado, LinhaCustoUnitarioExecucaoDF)

    def test_instance_of_criar_linha_subtotal_atividade_auxiliar( self ):
        _dfr_insumo = self.obj_ComposicaoDF.dfr_insumo.query( '{} == {}'.format(self.obj_ComposicaoDF.obj_col_dfr.grupo, self.obj_grupo.subtotal_unitario_atividade_auxiliar ) ) 
        resultado = self.obj_ComposicaoDF.criar_linha_subtotal_atividade_auxiliar( _dfr_insumo, self.obj_ComposicaoDF.composicao, self.obj_ComposicaoDF.obj_col_dfr )
        self.assertIsInstance( resultado, LinhaAtividadeAuxiliarDF)

    def test_instance_of_criar_linha_subtotal_tempo_fixo( self ):
        _dfr_insumo = self.obj_ComposicaoDF.dfr_insumo.query( '{} == {}'.format(self.obj_ComposicaoDF.obj_col_dfr.grupo, self.obj_grupo.subtotal_unitario_tempo_fixo ) ) 
        resultado = self.obj_ComposicaoDF.criar_linha_subtotal_tempo_fixo( _dfr_insumo, self.obj_ComposicaoDF.composicao, self.obj_ComposicaoDF.obj_col_dfr )
        self.assertIsInstance( resultado, LinhaTempoFixoDF)

    def test_instance_of_criar_linha_subtotal_transporte( self ):
        _dfr_insumo = self.obj_ComposicaoDF.dfr_insumo.query( '{} == {}'.format(self.obj_ComposicaoDF.obj_col_dfr.grupo, self.obj_grupo.subtotal_unitario_transporte ) )
        resultado = self.obj_ComposicaoDF.criar_linha_subtotal_transporte( _dfr_insumo, self.obj_ComposicaoDF.composicao, self.obj_ComposicaoDF.obj_col_dfr )
        self.assertIsInstance( resultado, LinhaTransporteDF)

    def test_instance_of_criar_linha_custo_unitario_direto_total( self ):
        _dfr_insumo = self.obj_ComposicaoDF.dfr_insumo.query( '{} == {}'.format(self.obj_ComposicaoDF.obj_col_dfr.grupo, self.obj_grupo.total_unitario_direto ) ) 
        resultado = self.obj_ComposicaoDF.criar_linha_custo_direto_total( _dfr_insumo, self.obj_ComposicaoDF.composicao, self.obj_ComposicaoDF.obj_col_dfr )
        self.assertIsInstance( resultado, LinhaCustoUnitarioDiretoTotalDF)

    def test_result_of_calcular_subtotal_equipamento( self ):
        _dfr_insumo_eq = self.obj_ComposicaoDF.obter_dfr_equipamento()
        obj_linha_eq = self.obj_ComposicaoDF.criar_linha_subtotal_equipamento( _dfr_insumo_eq, self.obj_ComposicaoDF.composicao, self.obj_ComposicaoDF.obj_col_dfr )
        resultado = obj_linha_eq.total
        self.assertEqual( resultado, self.obj_ComposicaoDF.composicao.custo_horario_equipamento) 

    def test_result_of_calcular_subtotal_mao_de_obra( self ):
        _dfr_insumo = self.obj_ComposicaoDF.dfr_insumo.query( '{} == {}'.format(self.obj_ComposicaoDF.obj_col_dfr.grupo, self.obj_grupo.insumo_mao_de_obra ) )
        resultado = round(_dfr_insumo[ self.obj_col_dfr.custo_total ].sum(), self.obj_precisao._04_algarismos)
        self.assertEqual( resultado, self.obj_ComposicaoDF.composicao.custo_horario_mao_de_obra)

    def test_result_of_calcular_custo_horario_execucao( self ):
        _dfr_insumo = self.obj_ComposicaoDF.dfr_insumo.query( '{} == {}'.format(self.obj_ComposicaoDF.obj_col_dfr.grupo, self.obj_grupo.subtotal_execucao ) )
        resultado = round( _dfr_insumo[ self.obj_col_dfr.custo_total ].sum(), self.obj_precisao._04_algarismos)
        self.assertEqual( resultado, self.obj_ComposicaoDF.composicao.custo_execucao)

    def test_result_of_calcular_custo_unitario_execucao( self ):
        _dfr_insumo = self.obj_ComposicaoDF.dfr_insumo.query( '{} == {}'.format(self.obj_ComposicaoDF.obj_col_dfr.grupo, self.obj_grupo.subtotal_unitario_execucao ) )
        resultado = round( _dfr_insumo[ self.obj_col_dfr.custo_total ].sum(), self.obj_precisao._04_algarismos)
        self.assertEqual( resultado, self.obj_ComposicaoDF.composicao.custo_unitario_execucao)




if __name__ == '__main__':
    unittest.main()