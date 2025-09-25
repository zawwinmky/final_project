
        document.addEventListener('DOMContentLoaded', async function () {
            const emailViewer = document.getElementById("emailViewer");
            emailViewer.addEventListener('click', async function (event){
                
                const row = event.target.closest('tr');
                if (row){
                    const mailId = row.dataset.mailId;
                    try{
                        const response = await fetch(`get_email/${mailId}`,{
                            method: 'POST',
                            headers: {
                                'Content-Type':'application/json'
                            },
                            body : JSON.stringify({email_id:mailId})
                        });

                        const data = await response.json();

                        if (response.ok)
                        {
                            let emailDetail = document.getElementById('emailDetail');
                            let html = '';
                            html = `<div class='row d-flex justify-content-center'><div class="col-8 border rounded text-start"> From:Name: Email: <br> To: Name: Email: <br> Subject: <br> Body: <br> </div></div>`;
                            emailDetail.innerHTML = html;
                        } else 
                        {
                            throw new Error(data.message);
                        }
                    } catch (error){
                        alert(error.message);
                        console.error(error.message);
                    }
                }
            });
        });
