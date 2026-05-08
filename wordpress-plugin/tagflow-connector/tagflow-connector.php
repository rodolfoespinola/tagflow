<?php
/**
 * Plugin Name: ALESC Media Connector
 * Description: Preenche automaticamente campos de mídia a partir do nome do arquivo
 * Version: 1.6
 * Author: Agência ALESC
 * Requires PHP: 7.2
 */

if (!defined('ABSPATH')) {
    exit;
}

// ─── DADOS DE CONFIGURAÇÃO ────────────────────────────────────────────────────

function alesc_fotografos() {
    static $cache = null;
    if ($cache === null) {
        $cache = array(
            'BC'  => 'Bruno Collaço/Agência Alesc',
            'DC'  => 'Daniel Conzi/Agência Alesc',
            'LGD' => 'Lucas Gabriel Diniz/Agência Alesc',
            'RC'  => 'Rodrigo Coelho/Agência Alesc',
            'AQ'  => 'Ana Quinto/Agência Alesc',
            'JB'  => 'Jefferson Baldo/Agência Alesc',
        );
    }
    return $cache;
}

function alesc_tipos_evento() {
    static $cache = null;
    if ($cache === null) {
        $cache = array(
            'S-ORDINARIA' => 'Sessão Ordinária',
            'S-ESPECIAL'  => 'Sessão Especial',
            'S-SOLENE'    => 'Sessão Solene',
            'PAB'         => 'Programa Antonieta de Barros',
            'COMISSAO'    => 'Comissão',
            'AUDIENCIA'   => 'Audiência Pública',
            'SEMINARIO'   => 'Seminário',
            'CURSO'       => 'Curso',
            'ENTREVISTA'  => 'Entrevista',
            'PODCAST'     => 'Podcast',
            'ESPECIAL'    => 'Matéria Especial',
            'MOCAO'       => 'Moção de Aplauso',
            'PRESIDENCIA' => 'Presidência',
            'SUSPENSAO'   => 'Suspensão de Sessão',
            'LITERARIO'   => 'Lançamento Literário',
            'EXPOARTE'    => 'Exposição de Arte',
            'CULTURAL'    => 'Evento Cultural',
        );
    }
    return $cache;
}

function alesc_comissoes() {
    static $cache = null;
    if ($cache === null) {
        $cache = array(
            'CCJ'                    => 'Comissão de Constituição e Justiça',
            'AGRICULTURA'            => 'Comissão de Agricultura e Desenvolvimento Rural',
            'ASSUNTOS-MUNICIPAIS'    => 'Comissão de Assuntos Municipais',
            'BEM-ESTAR-ANIMAL'       => 'Comissão de Bem-Estar Animal',
            'COMBATE-AS-DROGAS'      => 'Comissão de Combate às Drogas',
            'DEFESA-CIVIL'           => 'Comissão de Defesa Civil',
            'DIREITOS-HUMANOS'       => 'Comissão de Direitos Humanos e Família',
            'ECONOMIA'               => 'Comissão de Economia',
            'EDUCACAO'               => 'Comissão de Educação e Cultura',
            'ESPORTE'                => 'Comissão de Esporte',
            'ETICA'                  => 'Comissão de Ética',
            'MEIO-AMBIENTE'          => 'Comissão de Meio Ambiente',
            'PESCA'                  => 'Comissão de Pesca e Aquicultura',
            'SEGURANCA'              => 'Comissão de Segurança Pública',
            'TRABALHO'               => 'Comissão de Trabalho',
            'TRANSPORTE'             => 'Comissão de Transporte',
            'TURISMO'                => 'Comissão de Turismo',
            'CONSUMIDOR'             => 'Comissão dos Direitos do Consumidor',
            'CRIANCA-E-ADOLESCENTE'  => 'Comissão dos Direitos da Criança e do Adolescente',
            'PESSOA-COM-DEFICIENCIA' => 'Comissão dos Direitos da Pessoa com Deficiência',
            'PESSOA-IDOSA'           => 'Comissão dos Direitos da Pessoa Idosa',
            'MISTA'                  => 'Comissão Mista',
            'CPI'                    => 'Comissão Parlamentar de Inquérito',
        );
    }
    return $cache;
}

function alesc_municipios_dict() {
    static $cache = null;
    if ($cache === null) {
        $cache = array(
            'FLORIANOPOLIS'         => 'Florianópolis',
            'CHAPECO'               => 'Chapecó',
            'JOINVILLE'             => 'Joinville',
            'BLUMENAU'              => 'Blumenau',
            'ITAJAI'                => 'Itajaí',
            'CRICIUMA'              => 'Criciúma',
            'SAO-JOSE'              => 'São José',
            'LAGES'                 => 'Lages',
            'JARAGUA-DO-SUL'        => 'Jaraguá do Sul',
            'BALNEARIO-CAMBORIU'    => 'Balneário Camboriú',
            'BRUSQUE'               => 'Brusque',
            'TUBARAO'               => 'Tubarão',
            'CONCORDIA'             => 'Concórdia',
            'CACADOR'               => 'Caçador',
            'MAFRA'                 => 'Mafra',
            'CANOINHAS'             => 'Canoinhas',
            'SAO-BENTO-DO-SUL'      => 'São Bento do Sul',
            'RIO-DO-SUL'            => 'Rio do Sul',
            'BIGUACU'               => 'Biguaçu',
            'PALHOCA'               => 'Palhoça',
            'XANXERE'               => 'Xanxerê',
            'CURITIBANOS'           => 'Curitibanos',
            'ARARANGUA'             => 'Araranguá',
            'IMBITUBA'              => 'Imbituba',
            'LAGUNA'                => 'Laguna',
            'ORLEANS'               => 'Orleans',
            'URUSSANGA'             => 'Urussanga',
            'ICARA'                 => 'Içara',
            'JOACABA'               => 'Joaçaba',
            'VIDEIRA'               => 'Videira',
            'CAMPOS-NOVOS'          => 'Campos Novos',
            'HERVAL-DO-OESTE'       => 'Herval do Oeste',
            'TANGARA'               => 'Tangará',
            'SAO-MIGUEL-DO-OESTE'   => 'São Miguel do Oeste',
            'MARAVILHA'             => 'Maravilha',
            'PINHALZINHO'           => 'Pinhalzinho',
            'PALMITOS'              => 'Palmitos',
            'QUILOMBO'              => 'Quilombo',
            'SAO-LOURENCO-DO-OESTE' => 'São Lourenço do Oeste',
        );
    }
    return $cache;
}

// ─── HELPERS MULTIBYTE ────────────────────────────────────────────────────────

function alesc_strtolower($str) {
    if (extension_loaded('mbstring')) {
        return mb_strtolower($str, 'UTF-8');
    }
    return strtolower($str);
}

function alesc_ucwords($str) {
    if (extension_loaded('mbstring')) {
        return mb_convert_case($str, MB_CASE_TITLE, 'UTF-8');
    }
    return ucwords($str);
}

function alesc_formatar_texto($str) {
    return alesc_ucwords(alesc_strtolower(str_replace('-', ' ', $str)));
}

// ─── PARSER DO NOME DO ARQUIVO ────────────────────────────────────────────────
function alesc_parsear_filename($filename) {
    $nome   = strtoupper(pathinfo($filename, PATHINFO_FILENAME));
    $blocos = explode('_', $nome);

    $meta = array(
        'data'              => null,
        'ano'               => null,
        'mes'               => null,
        'tipo'              => null,
        'tipo_nome'         => null,
        'comissao'          => null,
        'descricao'         => null,
        'municipio'         => null,
        'fotografo'         => null,
        'sequencial'        => null,
        'filename_original' => $filename,
    );

    $meses = array(
        '01' => 'Janeiro',   '02' => 'Fevereiro', '03' => 'Março',
        '04' => 'Abril',     '05' => 'Maio',       '06' => 'Junho',
        '07' => 'Julho',     '08' => 'Agosto',     '09' => 'Setembro',
        '10' => 'Outubro',   '11' => 'Novembro',   '12' => 'Dezembro',
    );

    // Bloco 0 — data AAAA-MM-DD
    if (!empty($blocos[0]) && preg_match('/^(\d{4})-(\d{2})-(\d{2})$/', $blocos[0], $m)) {
        $meta['data'] = $m[3] . '/' . $m[2] . '/' . $m[1];
        $meta['ano']  = $m[1];
        $meta['mes']  = isset($meses[$m[2]]) ? $meses[$m[2]] : $m[2];
        array_shift($blocos);
    }

    // Último bloco — COD-SEQ (ex: BC-001, LGD-1, JB-22)
    if (!empty($blocos)) {
        $ultimo = end($blocos);
        if (preg_match('/^([A-Z]{2,3})-(\d+)$/', $ultimo, $m)) {
            $fotografos         = alesc_fotografos();
            $codigo             = $m[1];
            $meta['sequencial'] = $m[2];
            $meta['fotografo']  = isset($fotografos[$codigo])
                                  ? $fotografos[$codigo]
                                  : null;
            array_pop($blocos);
        }
    }

    // Bloco 1 — tipo do evento
    if (!empty($blocos)) {
        $tipos = alesc_tipos_evento();
        $tipo  = array_shift($blocos);

        if ($tipo === 'COMISSAO' && !empty($blocos)) {
            $comissoes         = alesc_comissoes();
            $subtipo           = array_shift($blocos);
            $meta['tipo']      = 'COMISSAO';
            $meta['tipo_nome'] = 'Comissão';
            $meta['comissao']  = isset($comissoes[$subtipo])
                                 ? $comissoes[$subtipo]
                                 : alesc_ucwords(alesc_strtolower(str_replace('-', ' ', $subtipo)));
        } else {
            $meta['tipo']      = $tipo;
            $meta['tipo_nome'] = isset($tipos[$tipo]) ? $tipos[$tipo] : null;
        }
    }

    // Blocos restantes — município com prefixo MUN- e descrição
    $municipios_dict  = alesc_municipios_dict();
    $descricao_blocos = array();

    foreach ($blocos as $bloco) {
        if (strpos($bloco, 'MUN-') === 0) {
            $municipio_raw     = substr($bloco, 4);
            $meta['municipio'] = isset($municipios_dict[$municipio_raw])
                                 ? $municipios_dict[$municipio_raw]
                                 : alesc_formatar_texto($municipio_raw);
        } else {
            $descricao_blocos[] = $bloco;
        }
    }

    if (!empty($descricao_blocos)) {
        $meta['descricao'] = alesc_ucwords(alesc_strtolower(
            implode(' ', array_map(function($b) {
                return str_replace('-', ' ', $b);
            }, $descricao_blocos))
        ));
    }

    return $meta;
}

// ─── HOOK PRINCIPAL ───────────────────────────────────────────────────────────
function alesc_processar_upload($metadata, $attachment_id) {

    // Verifica MIME type — mais robusto que wp_attachment_is_image() isolado
    $mime = get_post_mime_type($attachment_id);
    if (!$mime || strpos($mime, 'image/') !== 0) {
        return $metadata;
    }

    // Verifica caminho do arquivo antes de qualquer operação
    $arquivo = get_attached_file($attachment_id);
    if (!$arquivo) {
        error_log('ALESC Media Connector: arquivo não encontrado — attachment_id ' . $attachment_id);
        return $metadata;
    }

    // Trava anti-reprocessamento
    // Evita sobrescrever campos editados manualmente e reprocessamento
    // por plugins de regeneração de thumbnails (ex: Regenerate Thumbnails)
    if (get_post_meta($attachment_id, '_alesc_processado', true)) {
        return $metadata;
    }

    $filename = basename($arquivo);
    $meta     = alesc_parsear_filename($filename);

    // Arquivo fora do padrão — ignora sem poluir o banco
    if (empty($meta['tipo_nome'])) {
        error_log('ALESC Media Connector: nomenclatura não reconhecida — ' . $filename);
        return $metadata;
    }

    error_log('ALESC Media Connector: processando — ' . $filename . ' → ' . $meta['tipo_nome']);

    // ── Título ────────────────────────────────────────────────────────────────
    $partes_titulo = array_filter(array(
        $meta['tipo_nome'],
        $meta['comissao'],
        $meta['descricao'],
        $meta['data'] ? '— ' . $meta['data'] : null,
    ));
    $titulo = implode(' ', $partes_titulo);

    // ── Legenda ───────────────────────────────────────────────────────────────
    $legenda = !empty($meta['fotografo'])
               ? 'Foto: ' . $meta['fotografo']
               : '';

    // ── Alt text ──────────────────────────────────────────────────────────────
    $partes_alt = array_filter(array(
        $meta['tipo_nome'],
        !empty($meta['comissao']) ? $meta['comissao'] : $meta['descricao'],
        !empty($meta['municipio']) ? 'em ' . $meta['municipio'] : null,
        '— Assembleia Legislativa de Santa Catarina',
    ));
    $alt_text = sanitize_text_field(implode(' ', $partes_alt));

    // ── Campos nativos — wp_update_post sanitiza internamente ─────────────────
    if (!empty($alt_text)) {
        update_post_meta($attachment_id, '_wp_attachment_image_alt', $alt_text);
    }

    $post_data = array('ID' => $attachment_id);
    if (!empty($titulo))  $post_data['post_title']  = $titulo;
    if (!empty($legenda)) $post_data['post_excerpt'] = $legenda;

    $update_ok = true;
    if (count($post_data) > 1) {
        remove_filter('wp_generate_attachment_metadata', 'alesc_processar_upload', 10);
        $result = wp_update_post($post_data, true);
        add_filter('wp_generate_attachment_metadata', 'alesc_processar_upload', 10, 2);

        if (is_wp_error($result)) {
            error_log('ALESC Media Connector: erro em wp_update_post — ' . $result->get_error_message());
            $update_ok = false;
        }
    }

    // ── Campos customizados ───────────────────────────────────────────────────
    // Adaptar os meta_keys conforme os campos do WordPress da ALESC

    // Rastreabilidade — salvo sempre, meta_key fixo
    update_post_meta(
        $attachment_id,
        'alesc_filename_original',
        sanitize_text_field($filename)
    );

    if (!empty($meta['fotografo'])) {
        update_post_meta(
            $attachment_id,
            'fotografo', // adaptar
            sanitize_text_field($meta['fotografo'])
        );
    }
    if (!empty($meta['data'])) {
        update_post_meta(
            $attachment_id,
            'alesc_data', // adaptar
            sanitize_text_field($meta['data'])
        );
    }
    if (!empty($meta['tipo_nome'])) {
        update_post_meta(
            $attachment_id,
            'alesc_evento', // adaptar
            sanitize_text_field($meta['tipo_nome'])
        );
    }
    if (!empty($meta['comissao'])) {
        update_post_meta(
            $attachment_id,
            'alesc_comissao', // adaptar
            sanitize_text_field($meta['comissao'])
        );
    }
    if (!empty($meta['municipio'])) {
        update_post_meta(
            $attachment_id,
            'alesc_municipio', // adaptar
            sanitize_text_field($meta['municipio'])
        );
    }
    if (!empty($meta['ano'])) {
        update_post_meta(
            $attachment_id,
            'alesc_ano', // adaptar
            sanitize_text_field($meta['ano'])
        );
    }

    // Marca como processado apenas se wp_update_post foi bem-sucedido
    // Evita attachment marcado como processado com metadados incompletos
    if ($update_ok) {
        update_post_meta($attachment_id, '_alesc_processado', 1);
        error_log('ALESC Media Connector: concluído — attachment_id ' . $attachment_id);
    } else {
        error_log('ALESC Media Connector: processamento parcial — attachment_id ' . $attachment_id);
    }

    return $metadata;
}

add_filter('wp_generate_attachment_metadata', 'alesc_processar_upload', 10, 2);