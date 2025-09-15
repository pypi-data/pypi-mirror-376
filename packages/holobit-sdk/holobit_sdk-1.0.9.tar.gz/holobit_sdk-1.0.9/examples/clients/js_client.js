import fetch from 'node-fetch';

const url = process.env.HOLOBIT_API_URL || 'http://localhost:8000';
const user = process.env.HOLOBIT_USER || 'user';
const pass = process.env.HOLOBIT_PASSWORD || 'pass';
const auth = Buffer.from(`${user}:${pass}`).toString('base64');

async function main() {
  const compileRes = await fetch(`${url}/compile`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Basic ${auth}`
    },
    body: JSON.stringify({ code: 'print("Hola Holobit")' })
  });
  const { job_id } = await compileRes.json();
  console.log('Job ID:', job_id);

  const execRes = await fetch(`${url}/execute`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Basic ${auth}`
    },
    body: JSON.stringify({ job_id })
  });
  const result = await execRes.json();
  console.log('Resultado:', result);
}

main().catch(console.error);
