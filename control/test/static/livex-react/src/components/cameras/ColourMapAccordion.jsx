import React from 'react';
import { Accordion, Card, Button, InputGroup } from 'react-bootstrap';
import { WithEndpoint } from 'odin-react';
const EndPointButton = WithEndpoint(Button);

function ColourMapAccordion(props) {
    const {liveViewEndPoint} = props;
    const {index} = props;
    const indexString = index.toString();

    const colourEffects = [
        'autumn', 'bone', 'jet', 'winter', 'rainbow', 'ocean', 'summer', 'spring',
        'cool', 'hsv', 'pink', 'hot', 'parula', 'magma', 'inferno', 'plasma',
        'viridis', 'cividis', 'twilight', 'twilight_shifted', 'turbo', 'deepgreen'
    ];

    return (
        <InputGroup className="mb-3">
            <InputGroup.Text>Image Colour Map</InputGroup.Text>
            <Accordion defaultActiveKey="0">
                <Card>
                    <Accordion.Item eventKey="0">
                        <Accordion.Header>Current: {liveViewEndPoint?.data.image?.colour}</Accordion.Header>
                        <Accordion.Body>
                            {colourEffects.map((effect, index) => (
                                <EndPointButton
                                    key={index}
                                    variant="secondary"
                                    className="me-2 mb-2"
                                    endpoint={liveViewEndPoint}
                                    fullpath={"image/colour"}
                                    event_type="click"
                                    value={effect}>
                                        {effect}
                                </EndPointButton>
                            ))}
                        </Accordion.Body>
                    </Accordion.Item>
                </Card>
            </Accordion>
        </InputGroup>
    );
}

export default ColourMapAccordion;
