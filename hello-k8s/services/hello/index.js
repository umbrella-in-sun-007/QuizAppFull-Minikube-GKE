const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;
const GREETING = process.env.GREETING || 'Hello';

app.get('/greet', (req, res) => {
  res.json({ greeting: GREETING });
});

app.get('/health', (req, res) => res.send('ok'));

app.listen(PORT, () => console.log(`hello-service listening ${PORT}`));
