
document.addEventListener('DOMContentLoaded', async function () {
    const emailViewer = document.getElementById("emailViewer");
    emailViewer.addEventListener('click', async function (event) {
        const row = event.target.closest('tr');
        if (row) {
            const mailId = row.dataset.mailId;
            try {
                const response = await fetch(`email_detail/${mailId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email_id: mailId })
                });

                const data = await response.json();

                if (response.ok) {
                    const modalBody = document.getElementById('modalEmailBody');
                    const modalSubjectBody = document.getElementById('modalBodySubject');
                    const modalSenderName = document.getElementById('modalSenderName');
                    const modalSenderEmail = document.getElementById('modalSenderEmail');
                    const modalReceiverName = document.getElementById('modalReceiverName');
                    const modalReceiverEmail = document.getElementById('modalReceiverEmail');

                    if (data.subject) modalSubjectBody.textContent = data.subject;
                    if (data.body) modalBody.textContent = data.body;
                    if (modalSenderName && data.sender_name) modalSenderName.textContent = data.sender_name;
                    if (modalSenderEmail && data.sender_email) modalSenderEmail.textContent = data.sender_email;
                    if (modalReceiverName && data.receiver_name) modalReceiverName.textContent = data.receiver_name;
                    if (modalReceiverEmail && data.receiver_email) modalReceiverEmail.textContent = data.receiver_email;


                    const modalElement = document.getElementById('emailModal');
                    if (modalElement && typeof bootstrap !== 'undefined') {
                        const emailModal = new bootstrap.Modal(modalElement);
                        emailModal.show();
                    }

                } else {
                    throw new Error(data.message);
                }
            } catch (error) {
                alert(error.message);
                console.error(error.message);
            }
        }
    });
});
