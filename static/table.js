async function generateBooksTable() {
    try {
        const response = await fetch('/searched_books');
        const data = await response.json();

        const table = $('#books-table');
        table.empty(); // Clear existing rows

        // Generate and insert the table head
        const tableHead = $('<thead>').html(`
            <tr>
                <th>#</th>
                <th>Title</th>
                <th>Author(s)</th>
                <th>Found in A</th>
                <th>Found in B</th>
            </tr>
        `);
        table.append(tableHead);

        let rowNumber = 1; // Initialize the row number

        data.searchedBooks.forEach(book => {
            const row = $('<tr>');
            const isFoundAIcon = book.is_found_a ? '✓' : '✗';
            const isFoundBIcon = book.is_found_b ? '✓' : '✗';
            const isFoundAColor = book.is_found_a ? 'green' : 'red';
            const isFoundBColor = book.is_found_b ? 'green' : 'red';

            row.html(`
                <td>${rowNumber}</td>
                <td>${book.title}</td>
                <td>${book.authors}</td>
                <td style="color: ${isFoundAColor}; font-size: 25px; text-align: center;">${isFoundAIcon}</td>
                <td style="color: ${isFoundBColor}; font-size: 25px; text-align: center;">${isFoundBIcon}</td>
            `);
            table.append(row);

            rowNumber++; // Increment the row number for the next row
        });
    } catch (error) {
        console.error('Error fetching selected books:', error);
    }
}
