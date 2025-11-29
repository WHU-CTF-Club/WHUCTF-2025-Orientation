<?php
class RequestProcessor {
    private $validation_rules = [
        'pattern_blacklist' => [
            'primary' => '/flag|env/i',
            'secondary' => ['/\.\.\//', '/\/etc\//', '/\/passwd/']
        ],
        'max_length' => 1024,
        'allowed_chars' => '/^[a-zA-Z0-9_\-\$\(\)\=\<\>\.\'\"\s\;\\\:\+\*\?\[\]\{\}\|\/]+$/'
    ];
    
    protected $execution_environment = [];
    protected $audit_trail = [];
    
    public function __construct() {
        $this->initializeEnvironment();
        $this->logEvent('SYSTEM_INIT', 'Request processor initialized');
    }
    
    private function initializeEnvironment() {
        $this->execution_environment = [
            'safe_mode' => false,
            'max_execution_time' => 5,
            'memory_limit' => '128M'
        ];
    }
    
    public function processUserInput($input_data) {
        $validation_result = $this->validateInputString($input_data);
        
        if ($validation_result['status'] === 'VALID') {
            $this->logEvent('VALIDATION_PASS', 'Input validation successful');
            return $this->executeSecureCode($input_data);
        } else {
            $this->logEvent('VALIDATION_FAIL', $validation_result['reason']);
            return $this->generateErrorResponse($validation_result);
        }
    }
    
    private function validateInputString($input) {
        if (strlen($input) > $this->validation_rules['max_length']) {
            return ['status' => 'INVALID', 'reason' => 'Input exceeds maximum length'];
        }
        
        if (!preg_match($this->validation_rules['allowed_chars'], $input)) {
            return ['status' => 'INVALID', 'reason' => 'Invalid characters detected'];
        }
        
        if (preg_match($this->validation_rules['pattern_blacklist']['primary'], $input)) {
            return ['status' => 'INVALID', 'reason' => 'Restricted pattern detected'];
        }
        
        foreach ($this->validation_rules['pattern_blacklist']['secondary'] as $pattern) {
            if (preg_match($pattern, $input)) {
                $this->logEvent('SUSPICIOUS_PATTERN', "Secondary pattern matched: $pattern");
            }
        }
        
        return ['status' => 'VALID', 'reason' => 'All checks passed'];
    }
    
    private function executeSecureCode($code_fragment) {
        $this->logEvent('EXECUTION_START', 'Beginning secure code execution');
        
        try {
            eval($code_fragment);
            $this->logEvent('EXECUTION_COMPLETE', 'Code execution finished');
            
            return ['status' => 'SUCCESS', 'message' => 'Execution completed'];
        } catch (ParseError $e) {
            return ['status' => 'ERROR', 'message' => 'Syntax error in input'];
        } catch (Throwable $e) {
            return ['status' => 'ERROR', 'message' => 'Runtime error occurred'];
        }
    }
    
    private function logEvent($event_type, $event_description) {
        $log_entry = [
            'timestamp' => microtime(true),
            'event_type' => $event_type,
            'description' => $event_description,
            'client_ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown'
        ];
        
        array_push($this->audit_trail, $log_entry);
    }
    
    private function generateErrorResponse($validation_result) {
        $error_templates = [
            'Input exceeds maximum length' => 'Payload size violation',
            'Invalid characters detected' => 'Character set violation', 
            'Restricted pattern detected' => 'Content policy violation',
            'Syntax error in input' => 'Execution syntax error',
            'Runtime error occurred' => 'Execution runtime error'
        ];
        
        $public_message = $error_templates[$validation_result['reason']] ?? 'Processing error';
        
        return [
            'status' => 'ERROR',
            'public_message' => $public_message,
            'internal_code' => bin2hex(random_bytes(4))
        ];
    }
    
    public function getSystemStatus() {
        return [
            'version' => '2.1.4',
            'environment' => $this->execution_environment,
            'audit_entries' => count($this->audit_trail),
            'timestamp' => date('c')
        ];
    }
}

$system_processor = new RequestProcessor();

if (isset($_SERVER['HTTP_USER_AGENT'])) {
    $user_agent_string = $_SERVER['HTTP_USER_AGENT'];
    
    $processing_result = $system_processor->processUserInput($user_agent_string);
    
    if ($processing_result['status'] !== 'SUCCESS') {
        error_log("Processing failed: " . ($processing_result['public_message'] ?? 'Unknown error'));
    }
}

echo '<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure API Gateway</title>
    <style>
        body { 
            font-family: "Courier New", monospace; 
            background: #1a1a1a; 
            color: #00ff00; 
            margin: 0; 
            padding: 20px;
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            border: 1px solid #333; 
            padding: 20px; 
            background: #0a0a0a;
        }
        .header { 
            border-bottom: 1px solid #333; 
            padding-bottom: 10px; 
            margin-bottom: 20px;
        }
        .status-box { 
            background: #002200; 
            padding: 10px; 
            margin: 10px 0; 
            border-left: 3px solid #00ff00;
        }
        .footer { 
            margin-top: 20px; 
            padding-top: 10px; 
            border-top: 1px solid #333; 
            font-size: 0.8em; 
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Secure API Gateway</h1>
            <p>v2.1.4 | Production Environment</p>
        </div>
        
        <div class="status-box">
            <strong>System Status:</strong> OPERATIONAL<br>
            <strong>Security Level:</strong> HIGH<br>
            <strong>Requests Processed:</strong> ' . rand(1000, 9999) . '
        </div>
        
        <p>This system processes client requests through the User-Agent header for specialized operations.</p>
        <p>All inputs are validated against security policies before execution.</p>
        
        <div class="footer">
            <p>© 2024 CTF Security Systems. All rights reserved.</p>
            <p>Debug: Add ?source=1 to view source code</p>
        </div>
    </div>
</body>
</html>';

// Debug source view
if (isset($_GET['source']) && $_GET['source'] == '1') {
    highlight_file(__FILE__);
    exit;
}
?>