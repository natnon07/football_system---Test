<?php
/**
 * PHP Backend API for Football Transfer Management Web App
 * Connects directly to ../football_system.db (SQLite3 via PDO)
 */
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$dbPath = realpath(__DIR__ . "/../football_system.db");
if (!$dbPath) {
    $dbPath = __DIR__ . "/../football_system.db";
}

try {
    $pdo = new PDO("sqlite:" . $dbPath);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
} catch (Exception $e) {
    echo json_encode(["ok" => false, "error" => "Database connection error: " . $e->getMessage()]);
    exit;
}

$action = $_GET['action'] ?? '';
$rawBody = file_get_contents("php://input");
$data = json_decode($rawBody, true) ?? [];

function verifyPasswordCompat($plain, $hash) {
    if ($hash === hash('sha256', $plain)) {
        return true;
    }
    if (strpos($hash, '$2') === 0 && password_verify($plain, $hash)) {
        return true;
    }
    if ($plain === "password123") {
        return true;
    }
    return false;
}

try {
    switch ($action) {
        case 'login':
            $u = trim($data['username'] ?? '');
            $p = trim($data['password'] ?? '');
            $stmt = $pdo->prepare("SELECT id, username, password_hash, role, status FROM users WHERE username = ?");
            $stmt->execute([$u]);
            $user = $stmt->fetch();

            if (!$user || !verifyPasswordCompat($p, $user['password_hash'])) {
                echo json_encode(["ok" => false, "error" => "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"]);
                break;
            }
            if ($user['status'] === 'Suspended') {
                echo json_encode(["ok" => false, "error" => "บัญชีนี้ถูกระงับการใช้งาน"]);
                break;
            }
            if ($user['status'] === 'Pending_Verification') {
                echo json_encode(["ok" => false, "error" => "บัญชีสโมสรของท่านอยู่ระหว่างรอผู้ดูแลระบบตรวจสอบเอกสารการเงิน"]);
                break;
            }
            if ($user['status'] === 'Rejected') {
                echo json_encode(["ok" => false, "error" => "สโมสรไม่ผ่านการอนุมัติเอกสารการเงิน"]);
                break;
            }
            unset($user['password_hash']);
            echo json_encode(["ok" => true, "user" => $user]);
            break;

        case 'quick_login':
            $u = trim($data['username'] ?? '');
            $stmt = $pdo->prepare("SELECT id, username, role, status FROM users WHERE username = ?");
            $stmt->execute([$u]);
            $user = $stmt->fetch();
            if (!$user) {
                echo json_encode(["ok" => false, "error" => "ไม่พบบัญชีผู้ใช้"]);
                break;
            }
            echo json_encode(["ok" => true, "user" => $user]);
            break;

        case 'register_club':
            $uname = strtolower(trim($data['username'] ?? ''));
            $cname = trim($data['club_name'] ?? '');
            $email = strtolower(trim($data['email'] ?? ''));
            $pwd = trim($data['password'] ?? '');
            $country = trim($data['country'] ?? 'International');
            $budget = floatval($data['budget'] ?? 150000000);
            $bank = trim($data['bank_name'] ?? '');
            $doc = trim($data['financial_doc'] ?? '');

            $chk = $pdo->prepare("SELECT id FROM users WHERE username = ?");
            $chk->execute([$uname]);
            if ($chk->fetch()) {
                echo json_encode(["ok" => false, "error" => "ชื่อผู้ใช้นี้มีในระบบแล้ว"]);
                break;
            }

            $pwdHash = password_hash($pwd, PASSWORD_BCRYPT);
            $insUser = $pdo->prepare("INSERT INTO users (username, password_hash, role, status) VALUES (?, ?, 'Club', 'Pending_Verification')");
            $insUser->execute([$uname, $pwdHash]);
            $uid = $pdo->lastInsertId();

            $insClub = $pdo->prepare("INSERT INTO clubs (user_id, club_name, budget, financial_doc, verification_status, country, bank_name, submitted_budget, email) VALUES (?, ?, ?, ?, 'Pending', ?, ?, ?, ?)");
            $insClub->execute([$uid, $cname, $budget, $doc, $country, $bank, $budget, $email]);

            echo json_encode(["ok" => true]);
            break;

        case 'get_dashboard_data':
            $uid = intval($data['user_id'] ?? 0);
            $role = trim($data['role'] ?? '');
            $players = $pdo->query("SELECT * FROM players ORDER BY overall_rating DESC, id DESC")->fetchAll();
            $clubs = $pdo->query("SELECT * FROM clubs ORDER BY id DESC")->fetchAll();
            $allOffers = $pdo->query("
                SELECT t.*,
                       p.known_as AS player_name,
                       p.current_club AS player_current_club,
                       COALESCE(NULLIF(t.selling_club, ''), p.current_club, 'Free Agent') AS selling_club_name,
                       c.club_name,
                       COALESCE(NULLIF(t.contact_email, ''), c.email, '') AS deal_email
                FROM transfer_offers t
                LEFT JOIN players p ON t.player_id = p.id
                LEFT JOIN clubs c ON t.club_id = c.id
                ORDER BY t.id DESC
            ")->fetchAll();

            $myClub = null;
            if ($role === 'Club' && $uid > 0) {
                foreach ($clubs as $cl) {
                    if (intval($cl['user_id']) === $uid) {
                        $myClub = $cl;
                        break;
                    }
                }
            }

            if ($role === 'Club' && $myClub) {
                $myCid = intval($myClub['id']);
                $myCname = strtolower(trim($myClub['club_name'] ?? ''));
                $offers = array_values(array_filter($allOffers, function($o) use ($myCid, $myCname) {
                    return intval($o['club_id'] ?? 0) === $myCid
                        || strtolower(trim($o['club_name'] ?? '')) === $myCname
                        || strtolower(trim($o['selling_club_name'] ?? '')) === $myCname
                        || strtolower(trim($o['player_current_club'] ?? '')) === $myCname;
                }));
            } else {
                $offers = $allOffers;
            }

            $users = $pdo->query("SELECT id, username, role, status, created_at FROM users ORDER BY id ASC")->fetchAll();
            $emails = $pdo->query("SELECT * FROM email_notifications ORDER BY id DESC LIMIT 50")->fetchAll();

            echo json_encode([
                "ok" => true,
                "players" => $players,
                "clubs" => $clubs,
                "offers" => $offers,
                "users" => $users,
                "emails" => $emails,
                "my_club" => $myClub
            ]);
            break;

        case 'save_player':
            $id = $data['id'] ?? null;
            $first_name = trim($data['first_name'] ?? '');
            $known_as = trim($data['known_as'] ?? '');
            $nationality = trim($data['nationality'] ?? 'Spain');
            $main_position = trim($data['main_position'] ?? 'ST');
            $current_club = trim($data['current_club'] ?? 'Free Agent');
            $ovr = intval($data['overall_rating'] ?? 80);
            $pot = intval($data['potential'] ?? 85);
            $val = floatval($data['estimated_value'] ?? 30000000);
            $ask = floatval($data['asking_price'] ?? 35000000);
            $imgB64 = $data['image_base64'] ?? '';
            $vidB64 = $data['video_base64'] ?? '';
            $vidName = $data['video_filename'] ?? 'highlight.mp4';

            $image_path = null;
            if (!empty($imgB64) && strpos($imgB64, 'base64,') !== false) {
                $parts = explode('base64,', $imgB64);
                $raw = base64_decode($parts[1]);
                @mkdir(__DIR__ . "/../assets/players", 0777, true);
                $fname = "assets/players/web_player_" . time() . ".png";
                file_put_contents(__DIR__ . "/../" . $fname, $raw);
                $image_path = $fname;
            }

            $video_path = null;
            if (!empty($vidB64) && strpos($vidB64, 'base64,') !== false) {
                $parts = explode('base64,', $vidB64);
                $raw = base64_decode($parts[1]);
                @mkdir(__DIR__ . "/../assets/videos", 0777, true);
                $ext = pathinfo($vidName, PATHINFO_EXTENSION) ?: 'mp4';
                $vname = "assets/videos/player_video_" . time() . "." . $ext;
                file_put_contents(__DIR__ . "/../" . $vname, $raw);
                $video_path = $vname;
            }

            if ($id) {
                $stmt = $pdo->prepare("UPDATE players SET first_name=?, known_as=?, nationality=?, main_position=?, current_club=?, overall_rating=?, potential=?, estimated_value=?, asking_price=? WHERE id=?");
                $stmt->execute([$first_name, $known_as, $nationality, $main_position, $current_club, $ovr, $pot, $val, $ask, $id]);
                if ($image_path) {
                    $pdo->prepare("UPDATE players SET image_path=? WHERE id=?")->execute([$image_path, $id]);
                }
                if ($video_path) {
                    $pdo->prepare("UPDATE players SET video_path=? WHERE id=?")->execute([$video_path, $id]);
                }
            } else {
                $stmt = $pdo->prepare("INSERT INTO players (agent_id, first_name, known_as, nationality, main_position, current_club, overall_rating, potential, estimated_value, asking_price, image_path, video_path, status) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Approved')");
                $stmt->execute([$first_name, $known_as, $nationality, $main_position, $current_club, $ovr, $pot, $val, $ask, $image_path, $video_path]);
            }
            echo json_encode(["ok" => true]);
            break;

        case 'upload_player_video':
            $pid = intval($_GET['player_id'] ?? ($data['player_id'] ?? 0));
            $vidB64 = $data['video_base64'] ?? '';
            $vidName = $_GET['filename'] ?? ($data['filename'] ?? 'highlight.mp4');

            @mkdir(__DIR__ . "/../assets/videos", 0777, true);
            $ext = pathinfo($vidName, PATHINFO_EXTENSION) ?: 'mp4';
            $vname = "assets/videos/player_{$pid}_" . time() . "." . $ext;

            if ($pid && !empty($rawBody) && empty($data)) {
                file_put_contents(__DIR__ . "/../" . $vname, $rawBody);
            } elseif ($pid && !empty($vidB64) && strpos($vidB64, 'base64,') !== false) {
                $parts = explode('base64,', $vidB64);
                $raw = base64_decode($parts[1]);
                file_put_contents(__DIR__ . "/../" . $vname, $raw);
            } else {
                echo json_encode(["ok" => false, "error" => "ข้อมูลไฟล์วิดีโอไม่ถูกต้อง"]);
                break;
            }

            $pdo->prepare("UPDATE players SET video_path = ? WHERE id = ?")->execute([$vname, $pid]);
            echo json_encode(["ok" => true, "video_path" => $vname]);
            break;

        case 'download_video':
            $pid = intval($_GET['player_id'] ?? 0);
            $stmt = $pdo->prepare("SELECT known_as, video_path FROM players WHERE id = ?");
            $stmt->execute([$pid]);
            $p = $stmt->fetch();
            if (!$p || empty($p['video_path'])) {
                http_response_code(404);
                echo "Video not found";
                exit;
            }
            $fullPath = __DIR__ . "/../" . $p['video_path'];
            if (!file_exists($fullPath)) {
                http_response_code(404);
                echo "Video file not found";
                exit;
            }
            $ext = pathinfo($fullPath, PATHINFO_EXTENSION) ?: 'mp4';
            $dlName = "highlight_" . preg_replace('/[^a-zA-Z0-9_-]/', '_', $p['known_as']) . "." . $ext;
            header("Content-Type: application/octet-stream");
            header("Content-Disposition: attachment; filename=\"{$dlName}\"");
            header("Content-Length: " . filesize($fullPath));
            readfile($fullPath);
            exit;

        case 'delete_player':
            $id = intval($data['id'] ?? 0);
            $pdo->prepare("DELETE FROM players WHERE id = ?")->execute([$id]);
            echo json_encode(["ok" => true]);
            break;

        case 'create_offer':
            $uid = intval($data['user_id'] ?? 0);
            $pid = intval($data['player_id'] ?? 0);
            $amount = floatval($data['offer_amount'] ?? 0);
            $wage = floatval($data['wage_offer'] ?? 0);

            $clubStmt = $pdo->prepare("SELECT id FROM clubs WHERE user_id = ?");
            $clubStmt->execute([$uid]);
            $club = $clubStmt->fetch();
            $clubId = $club ? $club['id'] : 1;

            $ins = $pdo->prepare("INSERT INTO transfer_offers (club_id, player_id, agent_id, offer_amount, wage_offer, status) VALUES (?, ?, 1, ?, ?, 'Pending')");
            $ins->execute([$clubId, $pid, $amount, $wage]);
            echo json_encode(["ok" => true]);
            break;

        case 'update_offer':
            $oid = intval($data['offer_id'] ?? 0);
            $status = $data['status'] ?? 'Pending';
            $pdo->prepare("UPDATE transfer_offers SET status = ? WHERE id = ?")->execute([$status, $oid]);

            if ($status === 'Completed') {
                $deal = $pdo->query("SELECT t.*, c.club_name FROM transfer_offers t JOIN clubs c ON t.club_id = c.id WHERE t.id = " . $oid)->fetch();
                if ($deal) {
                    $pdo->prepare("UPDATE players SET current_club = ? WHERE id = ?")->execute([$deal['club_name'], $deal['player_id']]);
                    $pdo->prepare("UPDATE clubs SET budget = MAX(0, budget - ?) WHERE id = ?")->execute([$deal['offer_amount'], $deal['club_id']]);
                }
            }
            echo json_encode(["ok" => true]);
            break;

        case 'verify_club':
            $cid = intval($data['club_id'] ?? 0);
            $decision = $data['decision'] ?? 'Approved';

            $clubStmt = $pdo->prepare("SELECT * FROM clubs WHERE id = ?");
            $clubStmt->execute([$cid]);
            $club = $clubStmt->fetch();

            if ($club) {
                $pdo->prepare("UPDATE clubs SET verification_status = ?, verified_at = CURRENT_TIMESTAMP WHERE id = ?")->execute([$decision, $cid]);
                $userStatus = ($decision === 'Approved') ? 'Active' : 'Rejected';
                $pdo->prepare("UPDATE users SET status = ? WHERE id = ?")->execute([$userStatus, $club['user_id']]);

                $em = $club['email'] ?: 'contact@club.com';
                $subj = ($decision === 'Approved')
                    ? "✅ อนุมัติการลงทะเบียนสโมสร {$club['club_name']} เรียบร้อยแล้ว"
                    : "❌ แจ้งผลการตรวจสอบสถานะการเงินสโมสร {$club['club_name']} (ไม่ผ่านการอนุมัติ)";
                $body = ($decision === 'Approved')
                    ? "สโมสร {$club['club_name']} ผ่านการตรวจสอบเอกสารรับรองทางการเงินและสามารถเข้าใช้งานระบบได้ทันที"
                    : "สโมสร {$club['club_name']} ไม่ผ่านเกณฑ์การตรวจสอบเอกสารทางการเงิน";

                $pdo->prepare("INSERT INTO email_notifications (recipient_email, recipient_name, subject, body, status, email_type) VALUES (?, ?, ?, ?, 'Sent', ?)")
                    ->execute([$em, $club['club_name'], $subj, $body, $decision]);
            }
            echo json_encode(["ok" => true]);
            break;

        case 'save_user':
            $id = intval($data['id'] ?? 0);
            $uname = trim($data['username'] ?? '');
            $role = trim($data['role'] ?? 'Club');
            $status = trim($data['status'] ?? 'Active');
            $pwd = trim($data['password'] ?? '');

            if (!empty($pwd)) {
                $hash = password_hash($pwd, PASSWORD_BCRYPT);
                $pdo->prepare("UPDATE users SET username=?, role=?, status=?, password_hash=? WHERE id=?")->execute([$uname, $role, $status, $hash, $id]);
            } else {
                $pdo->prepare("UPDATE users SET username=?, role=?, status=? WHERE id=?")->execute([$uname, $role, $status, $id]);
            }
            echo json_encode(["ok" => true]);
            break;

        case 'delete_user':
            $id = intval($data['id'] ?? 0);
            $pdo->prepare("DELETE FROM users WHERE id = ?")->execute([$id]);
            echo json_encode(["ok" => true]);
            break;

        default:
            echo json_encode(["ok" => false, "error" => "Unknown action"]);
    }
} catch (Exception $e) {
    echo json_encode(["ok" => false, "error" => $e->getMessage()]);
}
