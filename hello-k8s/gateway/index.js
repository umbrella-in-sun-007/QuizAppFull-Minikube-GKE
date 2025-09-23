const express = require('express');
const axios = require('axios');
const app = express();
const PORT = process.env.PORT || 3002;

const HELLO_URL = process.env.HELLO_URL || 'http://localhost:3000/greet';
const WORLD_URL = process.env.WORLD_URL || 'http://localhost:3001/name';

app.get('/hello-world', async (req, res) => {
  try {
    const [h, w] = await Promise.all([
      axios.get(HELLO_URL),
      axios.get(WORLD_URL)
    ]);
    res.json({ message: `${h.data.greeting} ${w.data.name}` });
  } catch (err) {
    res.status(500).json({ error: String(err) });
  }
});

app.get('/health', (req, res) => res.send('ok'));

app.listen(PORT, () => console.log(`gateway listening ${PORT}`));
