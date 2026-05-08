<?php
/**
 * Plugin Name: Tagflow Connector
 * Description: Extrai metadados do nome do arquivo no upload — Agência ALESC
 * Version: 2.1
 * Author: Agência ALESC
 */

// ─── FOTÓGRAFOS ──────────────────────────────────────────────────────────────
define('TAGFLOW_FOTOGRAFOS', [
    'BC'  => 'Bruno Collaço/Agência Alesc',
    'DC'  => 'Daniel Conzi/Agência Alesc',
    'LGD' => 'Lucas Gabriel Diniz/Agência Alesc',
    'RC'  => 'Rodrigo Coelho/Agência Alesc',
    'AQ'  => 'Ana Quinto/Agência Alesc',
    'JB'  => 'Jefferson Baldo/Agência Alesc',
]);

// ─── TIPO DE EVENTO → NOME LEGÍVEL ───────────────────────────────────────────
define('TAGFLOW_TIPOS', [
    'PODCAST'      => 'Podcast',
    'CULTURAL'     => 'Evento Cultural',
    'CURSO'        => 'Curso',
    'AUDIENCIA'    => 'Audiência Pública',
    'ENTREVISTA'   => 'Entrevista',
    'EXPOARTE'     => 'Exposição de Arte',
    'LITERARIO'    => 'Lançamento Literário',
    'MOCAO'        => 'Moção de Aplauso',
    'SEMINARIO'    => 'Seminário',
    'SUSPENSAO'    => 'Suspensão de Sessão',
    'S-ESPECIAL'   => 'Sessão Especial',
    'S-ORDINARIA'  => 'Sessão Ordinária',
    'S-SOLENE'     => 'Sessão Solene',
    'PAB'          => 'Programa Antonieta de Barros',
    'PRESIDENCIA'  => 'Presidência',
    'ESPECIAL'     => 'Matéria Especial',
    'COMISSAO'     => 'Comissão',
]);

// ─── COMISSÕES ────────────────────────────────────────────────────────────────
define('TAGFLOW_COMISSOES', [
    'AGRICULTURA'            => 'Comissão de Agricultura e Desenvolvimento Rural',
    'ASSUNTOS-MUNICIPAIS'    => 'Comissão de Assuntos Municipais',
    'BEM-ESTAR-ANIMAL'       => 'Comissão de Bem-Estar Animal',
    'COMBATE-AS-DROGAS'      => 'Comissão de Combate às Drogas',
    'CCJ'                    => 'Comissão de Constituição e Justiça',
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
]);

// ─── PARSER DO NOME DO ARQUIVO ────────────────────────────────────────────────
function tagflow_parsear_filename($filename) {
    $nome   = strtoupper(pathinfo($filename, PATHINFO_FILENAME));
    $blocos = explode('_', $nome);

    $meta = [
        'data'       => null,
        'ano'        => null,
        'mes'        => null,
        'tipo'       => null,
        'tipo_nome'  => null,
        'comissao'   => null,
        'descricao'  => null,
        'municipio'  => null,
        'fotografo'  => null,
        'sequencial' => null,
    ];

    $meses = [
        '01' => 'Janeiro',  '02' => 'Fevereiro', '03' => 'Março',
        '04' => 'Abril',    '05' => 'Maio',       '06' => 'Junho',
        '07' => 'Julho',    '08' => 'Agosto',     '09' => 'Setembro',
        '10' => 'Outubro',  '11' => 'Novembro',   '12' => 'Dezembro',
    ];

    // Bloco 0 — data AAAA-MM-DD
    if (!empty($blocos[0]) && preg_match('/^(\d{4})-(\d{2})-(\d{2})$/', $blocos[0], $m)) {
        $meta['data'] = $m[3] . '/' . $m[2] . '/' . $m[1];
        $meta['ano']  = $m[1];
        $meta['mes']  = $meses[$m[2]] ?? $m[2];
        array_shift($blocos);
    }

    // Último bloco — COD-SEQ (ex: BC-001 ou LGD-042)
    if (!empty($blocos)) {
        $ultimo = end($blocos);
        if (preg_match('/^([A-Z]{2,3})-(\d+)$/', $ultimo, $m)) {
            $meta['sequencial'] = $m[2];
            $meta['fotografo']  = TAGFLOW_FOTOGRAFOS[$m[1]] ?? $m[1];
            array_pop($blocos);
        }
    }

    // Bloco 1 — tipo do evento
    if (!empty($blocos)) {
        $tipo = array_shift($blocos);

        // Comissão tem subtipo: COMISSAO_CCJ
        if ($tipo === 'COMISSAO' && !empty($blocos)) {
            $subtipo           = array_shift($blocos);
            $meta['tipo']      = 'COMISSAO';
            $meta['tipo_nome'] = 'Comissão';
            $meta['comissao']  = TAGFLOW_COMISSOES[$subtipo]
                                 ?? ucwords(strtolower(str_replace('-', ' ', $subtipo)));
        } else {
            $meta['tipo']      = $tipo;
            $meta['tipo_nome'] = TAGFLOW_TIPOS[$tipo]
                                 ?? ucwords(strtolower(str_replace('-', ' ', $tipo)));
        }
    }

    // Blocos restantes — descrição e município opcional
    if (!empty($blocos)) {
        // Município: último bloco quando há mais de um bloco restante
        if (count($blocos) > 1) {
            $meta['municipio'] = ucwords(strtolower(
                str_replace('-', ' ', array_pop($blocos))
            ));
        }
        $meta['descricao'] = ucwords(strtolower(
            implode(' ', array_map(fn($b) => str_replace('-', ' ', $b), $blocos))
        ));
    }

    return $meta;
}

// ─── GERAÇÃO DE CAMPOS AUTOMÁTICOS ───────────────────────────────────────────
function tagflow_gerar_campos($meta) {
    $campos = [];

    // Título
    $partes_titulo = array_filter([
        $meta['tipo_nome'],
        $meta['comissao'],
        $meta['descricao'],
        $meta['data'] ? '— ' . $meta['data'] : null,
    ]);
    $campos['titulo'] = implode(' ', $partes_titulo);

    // Legenda (crédito fotográfico)
    if ($meta['fotografo']) {
        $campos['legenda'] = 'Foto: ' . $meta['fotografo'];
    }

    // Alt text
    $partes_alt = array_filter([
        $meta['tipo_nome'],
        $meta['comissao'] ?? $meta['descricao'],
        $meta['municipio'] ? 'em ' . $meta['municipio'] : null,
        '— Assembleia Legislativa de Santa Catarina',
    ]);
    $campos['alt_text'] = implode(' ', $partes_alt);

    // Descrição
    $partes_desc = array_filter([
        $meta['tipo_nome'],
        $meta['comissao'],
        $meta['descricao'],
        $meta['municipio'] ? 'em ' . $meta['municipio'] : null,
        $meta['data'] ? 'realizado em ' . $meta['data'] : null,
        $meta['fotografo'] ? '| Foto: ' . $meta['fotografo'] : null,
    ]);
    $campos['descricao'] = implode(' ', $partes_desc);

    return $campos;
}

// ─── HOOK PRINCIPAL ───────────────────────────────────────────────────────────
function tagflow_processar_upload($attachment_id) {
    if (!wp_attachment_is_image($attachment_id)) return;

    $arquivo  = get_attached_file($attachment_id);
    $filename = basename($arquivo);
    $meta     = tagflow_parsear_filename($filename);
    $campos   = tagflow_gerar_campos($meta);

    // ── Campos nativos do WordPress ───────────────────────────────────────────
    if (!empty($campos['alt_text'])) {
        update_post_meta($attachment_id, '_wp_attachment_image_alt', $campos['alt_text']);
    }

    $post_data = ['ID' => $attachment_id];
    if (!empty($campos['titulo']))    $post_data['post_title']   = $campos['titulo'];
    if (!empty($campos['legenda']))   $post_data['post_excerpt'] = $campos['legenda'];
    if (!empty($campos['descricao'])) $post_data['post_content'] = $campos['descricao'];
    if (count($post_data) > 1) {
        wp_update_post($post_data);
    }

    // ── Campos customizados — adaptar meta_keys após resposta da desenvolvedora
    if (!empty($meta['fotografo'])) {
        update_post_meta($attachment_id, 'fotografo', $meta['fotografo']); // adaptar
    }
    if (!empty($meta['data'])) {
        update_post_meta($attachment_id, 'alesc_data', $meta['data']); // adaptar
    }
    if (!empty($meta['tipo_nome'])) {
        update_post_meta($attachment_id, 'alesc_evento', $meta['tipo_nome']); // adaptar
    }
    if (!empty($meta['comissao'])) {
        update_post_meta($attachment_id, 'alesc_comissao', $meta['comissao']); // adaptar
    }
    if (!empty($meta['municipio'])) {
        update_post_meta($attachment_id, 'alesc_municipio', $meta['municipio']); // adaptar
    }
    if (!empty($meta['ano'])) {
        update_post_meta($attachment_id, 'alesc_ano', $meta['ano']); // adaptar
    }

    // ── Fila SQLite para o worker Python (reconhecimento facial) ──────────────
    $fila_db = WP_CONTENT_DIR . '/tagflow-fila.db';
    try {
        $db = new PDO('sqlite:' . $fila_db);
        $db->exec("CREATE TABLE IF NOT EXISTS fila (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            attachment_id INTEGER,
            arquivo       TEXT,
            arquivo_hash  TEXT UNIQUE,
            status        TEXT DEFAULT 'pendente',
            criado_em     TEXT
        )");
        $stmt = $db->prepare(
            "INSERT OR IGNORE INTO fila
             (attachment_id, arquivo, arquivo_hash, criado_em)
             VALUES (?, ?, ?, ?)"
        );
        $stmt->execute([
            $attachment_id,
            $arquivo,
            md5($filename),
            date('Y-m-d H:i:s'),
        ]);
    } catch (Exception $e) {
        error_log('Tagflow Connector erro fila: ' . $e->getMessage());
    }
}

add_action('add_attachment', 'tagflow_processar_upload');