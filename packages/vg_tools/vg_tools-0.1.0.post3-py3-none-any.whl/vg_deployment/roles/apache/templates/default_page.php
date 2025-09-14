<?php
echo <<<HTML
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>VG_MANAGEMENT</title>
    <style>
        body {
            background: #f7f7fa;
            font-family: 'Segoe UI', Arial, sans-serif;
            color: #222;
            text-align: center;
            padding-top: 10%;
        }
        .container {
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            display: inline-block;
            padding: 40px 60px;
        }
        h1 {
            color: #47e32d;
            margin-bottom: 16px;
        }
        a {
            color: #47e32d;
            text-decoration: none;
            font-weight: bold;
        }
        a:hover {
            text-decoration: underline;
        }
        .logo {
            width: 80px;
            margin-bottom: 24px;
        }
    </style>
</head>
<body>
    <div class="container">
        <img class="logo" src="https://vnguru.com/assets/images/logo.png" alt="VG Logo" onerror="this.style.display='none'">
        <h1>Hello, this is default page</h1>
        <p>Visit our homepage: <a href="https://vnguru.com/" target="_blank">https://vnguru.com/</a></p>
    </div>
</body>
</html>
HTML;
