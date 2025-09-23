const express = require('express');
const app = express();
const PORT = process.env.PORT || 3001;
const NAME = process.env.NAME || 'World!';

app.get('/name', (req, res) => {
  res.json({ name: NAME });
});

app.get('/health', (req, res) => res.send('ok'));

app.listen(PORT, () => console.log(`world-service listening ${PORT}`));

