import pandas as pd
from projeto import (
                        Projeto,
                    )
from estrutura_dados import (
                        NohArvore,
                        NohPilha,
                        Pilha,
                        NohFila,
                        Fila,
                    )
from formatacao_dados import (
                        Codigo,
                        Escrita,
                        EscritaCabecalho,
                        ConfiguraDataFrame,
                    )
from escrita_resumo import (
                        FormatacaoEscritaCustoEquipamento,
                        FormatacaoEscritaCustoMaoDeObra,
                        FormatacaoEscritaCustoMaterial,
                        FormatacaoEscritaResumoTransporte,
                        FormatacaoEscritaResumoEquipamento,
                        FormatacaoEscritaResumoMaoDeObra,
                        FormatacaoEscritaResumoMaterial,
                        FormatacaoEscritaResumoServico,
                        FormatacaoEscritaResumoABCServico,
                        FormatacaoEscritaResumoABCEquipamento,
                        FormatacaoEscritaResumoABCMaoDeObra,
                        FormatacaoEscritaResumoABCMaterial,
                        FormatacaoABCCondicional,
                        FormatacaoABCCondicionalAcumulado,
                        FormatacaoABCCondicionalAcumuladoEquipamento,
                    )
from escrita_composicao import  (
                        FormatacaoComposicao,
                        FormatacaoCabecalho,
                        FormatacaoComposicaoCondicional,
                        FormatacaoComposicaoCondicionalNaoMostrar,
                    )


def escrever_arquivo_excel( arquivo, projeto: Projeto, maximo_linhas_na_composicao, dados_projeto ):
    obj_codigo = Codigo()
    dicionario = projeto.obter_dfr_composicao()
    numero_de_composicoes = len( dicionario )
    numero_linhas = numero_de_composicoes * maximo_linhas_na_composicao

    # contador para as linhas das composições
    linha_inicio = 1

    # cria um objeto Excel
    writer = pd.ExcelWriter( '{}.{}'.format( arquivo, 'xlsx' ), engine='xlsxwriter' )

    formato = FormatacaoComposicao( writer )

    ##### escreve resumo de serviços do projeto
    obj_format = FormatacaoEscritaResumoServico( writer )
    obj_configura_data_frame = ConfiguraDataFrame( projeto.obter_dfr_servicos_projeto(), obj_format)
    dfr_servico_resumo = obj_configura_data_frame.obter_data_frame_configurado()    
    obj_escrita = Escrita( obj_format, dados_projeto, dfr_servico_resumo.shape[0] )
    writer = obj_escrita.obter_escritor_configurado()
    ##### escreve curva abc de serviços das composições
    obj_format = FormatacaoEscritaResumoABCServico( writer )
    obj_configura_data_frame = ConfiguraDataFrame( projeto.obter_dfr_curva_abc_servico(), obj_format)
    dfr_curva_abc_servico = obj_configura_data_frame.obter_data_frame_configurado()    
    obj_escrita = Escrita( obj_format, dados_projeto, dfr_curva_abc_servico.shape[0] )
    writer = obj_escrita.obter_escritor_configurado()
    # formatando a coluna de percentual acumulado da curva ABC
    obj_formatacao_condicional_acumulado = FormatacaoABCCondicionalAcumulado( writer, obj_format.nome_tabela, projeto.numero_servico_unico )
    for item in obj_formatacao_condicional_acumulado.lista_entrada_formatacao:
        writer.sheets[ obj_format.nome_tabela ].conditional_format( obj_formatacao_condicional_acumulado.entrada_area_formatacao, {'type':'cell','criteria': item.criterio, 'minimum': item.value_min, 'maximum': item.value_max, 'format': item.formatacao_condicional} )
    # formatando a coluna de percentual da curva ABC
    obj_formatacao_condicional_percentual = FormatacaoABCCondicional( writer, obj_format.nome_tabela, projeto.numero_servico_unico )
    for item in obj_formatacao_condicional_percentual.lista_entrada_formatacao:
        writer.sheets[ obj_format.nome_tabela ].conditional_format( obj_formatacao_condicional_percentual.entrada_area_formatacao, {'type':'cell','criteria': item.criterio, 'value': item.value, 'format': item.formatacao_condicional} )


    ##### escreve custos de equipamentos das composições
    obj_format = FormatacaoEscritaCustoEquipamento( writer )
    obj_configura_data_frame = ConfiguraDataFrame( projeto.obter_dfr_equipamento(), obj_format)
    dfr_equipamento_custo = obj_configura_data_frame.obter_data_frame_configurado()
    obj_escrita = Escrita( obj_format, dados_projeto, dfr_equipamento_custo.shape[0] )
    writer = obj_escrita.obter_escritor_configurado()

    ##### escreve custos de mão de obra das composições
    obj_format = FormatacaoEscritaCustoMaoDeObra( writer )
    obj_configura_data_frame = ConfiguraDataFrame( projeto.obter_dfr_mao_de_obra(), obj_format)
    dfr_mao_de_obra_custo = obj_configura_data_frame.obter_data_frame_configurado()    
    obj_escrita = Escrita( obj_format, dados_projeto, dfr_mao_de_obra_custo.shape[0] )
    writer = obj_escrita.obter_escritor_configurado()

    ##### escreve custos de materiais das composições
    obj_format = FormatacaoEscritaCustoMaterial( writer )
    obj_configura_data_frame = ConfiguraDataFrame( projeto.obter_dfr_material(), obj_format)
    dfr_material_custo = obj_configura_data_frame.obter_data_frame_configurado()    
    obj_escrita = Escrita( obj_format, dados_projeto, dfr_material_custo.shape[0] )
    writer = obj_escrita.obter_escritor_configurado()

    ##### escreve utilizações de transportes das composições
    obj_format = FormatacaoEscritaResumoTransporte( writer )
    obj_configura_data_frame = ConfiguraDataFrame( projeto.obter_dfr_transporte_utilizacao(), obj_format)
    dfr_transporte_utilizacao = obj_configura_data_frame.obter_data_frame_configurado()    
    obj_escrita = Escrita( obj_format, dados_projeto, dfr_transporte_utilizacao.shape[0] )
    writer = obj_escrita.obter_escritor_configurado()

    ##### escreve utilizações de equipamentos das composições
    obj_format = FormatacaoEscritaResumoEquipamento( writer )
    obj_configura_data_frame = ConfiguraDataFrame( projeto.obter_dfr_equipamento_utilizacao(), obj_format)
    dfr_equipamento_utilizacao = obj_configura_data_frame.obter_data_frame_configurado()    
    obj_escrita = Escrita( obj_format, dados_projeto, dfr_equipamento_utilizacao.shape[0] )
    writer = obj_escrita.obter_escritor_configurado()
    ##### escreve curva abc de equipamentos das composições
    obj_format = FormatacaoEscritaResumoABCEquipamento( writer )
    obj_configura_data_frame = ConfiguraDataFrame( projeto.obter_dfr_curva_abc_equipamento(), obj_format)
    dfr_curva_abc_equipamento = obj_configura_data_frame.obter_data_frame_configurado()    
    obj_escrita = Escrita( obj_format, dados_projeto, dfr_curva_abc_equipamento.shape[0] )
    writer = obj_escrita.obter_escritor_configurado()
    # formatando a coluna de percentual acumulado da curva ABC
    obj_formatacao_condicional_acumulado = FormatacaoABCCondicionalAcumuladoEquipamento( writer, obj_format.nome_tabela, projeto.numero_equipamento_unico )
    for item in obj_formatacao_condicional_acumulado.lista_entrada_formatacao:
        writer.sheets[ obj_format.nome_tabela ].conditional_format( obj_formatacao_condicional_acumulado.entrada_area_formatacao, {'type':'cell','criteria': item.criterio, 'minimum': item.value_min, 'maximum': item.value_max, 'format': item.formatacao_condicional} )


    ##### escreve utilizações de mão de obra das composições
    obj_format = FormatacaoEscritaResumoMaoDeObra( writer )
    obj_configura_data_frame = ConfiguraDataFrame( projeto.obter_dfr_mao_de_obra_utilizacao(), obj_format)
    dfr_mao_de_obra_utilizacao = obj_configura_data_frame.obter_data_frame_configurado()    
    obj_escrita = Escrita( obj_format, dados_projeto, dfr_mao_de_obra_utilizacao.shape[0] )
    writer = obj_escrita.obter_escritor_configurado()
    ##### escreve curva abc de mão de obra das composições
    obj_format = FormatacaoEscritaResumoABCMaoDeObra( writer )
    obj_configura_data_frame = ConfiguraDataFrame( projeto.obter_dfr_curva_abc_mao_de_obra(), obj_format)
    dfr_curva_abc_mao_de_obra = obj_configura_data_frame.obter_data_frame_configurado()    
    obj_escrita = Escrita( obj_format, dados_projeto, dfr_curva_abc_mao_de_obra.shape[0] )
    writer = obj_escrita.obter_escritor_configurado()
    # formatando a coluna de percentual acumulado da curva ABC
    obj_formatacao_condicional_acumulado = FormatacaoABCCondicionalAcumulado( writer, obj_format.nome_tabela, projeto.numero_mao_de_obra_unica )
    for item in obj_formatacao_condicional_acumulado.lista_entrada_formatacao:
        writer.sheets[ obj_format.nome_tabela ].conditional_format( obj_formatacao_condicional_acumulado.entrada_area_formatacao, {'type':'cell','criteria': item.criterio, 'minimum': item.value_min, 'maximum': item.value_max, 'format': item.formatacao_condicional} )


    ##### escreve utilizações de materiais das composições
    obj_format = FormatacaoEscritaResumoMaterial( writer )
    obj_configura_data_frame = ConfiguraDataFrame( projeto.obter_dfr_material_utilizacao(), obj_format)
    dfr_material_utilizacao = obj_configura_data_frame.obter_data_frame_configurado()    
    obj_escrita = Escrita( obj_format, dados_projeto, dfr_material_utilizacao.shape[0] )
    writer = obj_escrita.obter_escritor_configurado()
    ##### escreve curva abc de material das composições
    obj_format = FormatacaoEscritaResumoABCMaterial( writer )
    obj_configura_data_frame = ConfiguraDataFrame( projeto.obter_dfr_curva_abc_material(), obj_format)
    dfr_curva_abc_material = obj_configura_data_frame.obter_data_frame_configurado()    
    obj_escrita = Escrita( obj_format, dados_projeto, dfr_curva_abc_material.shape[0] )
    writer = obj_escrita.obter_escritor_configurado()
    # formatando a coluna de percentual acumulado da curva ABC
    obj_formatacao_condicional_acumulado = FormatacaoABCCondicionalAcumulado( writer, obj_format.nome_tabela, projeto.numero_material_unico )
    for item in obj_formatacao_condicional_acumulado.lista_entrada_formatacao:
        writer.sheets[ obj_format.nome_tabela ].conditional_format( obj_formatacao_condicional_acumulado.entrada_area_formatacao, {'type':'cell','criteria': item.criterio, 'minimum': item.value_min, 'maximum': item.value_max, 'format': item.formatacao_condicional} )


    ##### escreve as composições
    for _df in dicionario.values():
        obj_configura_data_frame = ConfiguraDataFrame( _df.dfr_insumo, formato, linha_inicio)
        obj_formatacao_cabecalho = FormatacaoCabecalho( writer, _df.composicao, formato.nome_tabela )
        obj_escrita = EscritaCabecalho( obj_formatacao_cabecalho, linha_inicio )
        writer = obj_escrita.obter_escritor_configurado()
        _df.dfr_insumo = obj_configura_data_frame.obter_data_frame_configurado()
        linha_inicio = linha_inicio + maximo_linhas_na_composicao

    obj_escrita = Escrita( formato, dados_projeto, numero_linhas, numero_de_composicoes )
    writer = obj_escrita.obter_escritor_configurado()
    # formatando as linhas de custos horários e unitários
    obj_formatacao_condicional = FormatacaoComposicaoCondicional( writer, obj_codigo, numero_linhas, formato.nome_tabela )
    for item in obj_formatacao_condicional.lista_entrada_formatacao:
        writer.sheets[ formato.nome_tabela ].conditional_format( obj_formatacao_condicional.entrada_area_formatacao, {'type':'formula','criteria': item.criterio,'format': item.formatacao_condicional} )
    # formatando os códigos que não devem ser mostrados
    obj_formatacao_condicional_n_mostrar = FormatacaoComposicaoCondicionalNaoMostrar( writer, obj_codigo, numero_linhas, formato.nome_tabela )
    for item in obj_formatacao_condicional_n_mostrar.lista_entrada_formatacao:
        writer.sheets[ formato.nome_tabela ].conditional_format( obj_formatacao_condicional_n_mostrar.entrada_area_formatacao, {'type':'text','criteria':'containing','value': item.codigo,'format': item.formatacao_condicional} )



    writer.save()