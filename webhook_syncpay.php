<?php
/**
 * Webhook do SyncPay
 * Recebe notificações de pagamento confirmado
 */

// Configurações
define('SYNCPAY_CLIENT_SECRET', 'b6d75387-28ad-4ce1-83aa-96699c0c03da');
define('BOT_API_URL', 'http://localhost:5000/api/payment_confirmed'); // Ajustar para seu bot

// Log de entrada
file_put_contents('webhook_syncpay.log', date('Y-m-d H:i:s') . " - Webhook recebido\n", FILE_APPEND);

// Obter dados do POST
$input = file_get_contents('php://input');
file_put_contents('webhook_syncpay.log', "Payload: $input\n", FILE_APPEND);

// Decodificar JSON
$data = json_decode($input, true);

if (!$data) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON']);
    exit;
}

// Log dos dados recebidos
file_put_contents('webhook_syncpay.log', "Dados: " . print_r($data, true) . "\n", FILE_APPEND);

// Validar assinatura (se SyncPay enviar)
// TODO: Implementar validação de assinatura conforme documentação SyncPay

// Extrair informações do pagamento
$transaction_id = $data['identifier'] ?? $data['id'] ?? null;
$status = $data['status'] ?? 'unknown';
$amount = $data['amount'] ?? 0;

if (!$transaction_id) {
    http_response_code(400);
    echo json_encode(['error' => 'Transaction ID not found']);
    exit;
}

// Verificar se o pagamento foi aprovado
if ($status === 'paid' || $status === 'approved' || $status === 'confirmed') {
    
    // Notificar o bot via arquivo JSON (método alternativo se não tiver API)
    $payment_data = [
        'transaction_id' => $transaction_id,
        'status' => 'paid',
        'amount' => $amount,
        'gateway' => 'syncpay',
        'timestamp' => time(),
        'webhook_data' => $data
    ];
    
    // Salvar em arquivo para o bot processar
    $payments_file = 'confirmed_payments.json';
    $payments = [];
    
    if (file_exists($payments_file)) {
        $payments = json_decode(file_get_contents($payments_file), true) ?: [];
    }
    
    $payments[] = $payment_data;
    file_put_contents($payments_file, json_encode($payments, JSON_PRETTY_PRINT));
    
    // Log de sucesso
    file_put_contents('webhook_syncpay.log', "Pagamento confirmado: $transaction_id\n", FILE_APPEND);
    
    // Tentar notificar o bot via cURL (se tiver API)
    /*
    $ch = curl_init(BOT_API_URL);
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payment_data));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    $response = curl_exec($ch);
    curl_close($ch);
    */
    
    http_response_code(200);
    echo json_encode(['success' => true, 'message' => 'Payment processed']);
    
} else {
    // Pagamento não aprovado ainda
    file_put_contents('webhook_syncpay.log', "Status não confirmado: $status\n", FILE_APPEND);
    
    http_response_code(200);
    echo json_encode(['success' => true, 'message' => 'Status received']);
}

?>

